# EyeQ/image-filter-service/app/image_processing/image_filter.py
import cv2
import numpy as np
import albumentations as A
from app.config import STANDARD_SIZES

class ImageFilter:
    def __init__(self):
        self.standard_sizes = STANDARD_SIZES

    def resize_keep_ratio(self, img, class_name="autre"):
        """
        Redimensionne l'image en gardant le ratio, en utilisant la largeur cible de la classe.
        
        Args:
            img: Image à redimensionner (numpy array).
            class_name: Classe de l'image ("BS", "ordonnance", "facture", ou "autre").
        
        Returns:
            Image redimensionnée.
        """
        standard_size = self.standard_sizes.get(class_name, self.standard_sizes["autre"])
        target_width = standard_size[0]  # Largeur cible
        
        # Calculer le ratio pour garder les proportions
        if len(img.shape) == 3:
            h, w, _ = img.shape
        else:
            h, w = img.shape
        ratio = target_width / w
        height = int(h * ratio)
        
        # Redimensionner
        return cv2.resize(img, (target_width, height))

    def get_ratio(self, img, class_name="autre"):
        """
        Calcule le ratio entre l'image originale et redimensionnée.
        
        Args:
            img: Image d'entrée (numpy array).
            class_name: Classe de l'image ("BS", "ordonnance", "facture", ou "autre").
        
        Returns:
            Ratio (float).
        """
        standard_size = self.standard_sizes.get(class_name, self.standard_sizes["autre"])
        target_width = standard_size[0]
        return img.shape[1] / target_width

    def edgesDet(self, img, minVal=200, maxVal=250):
        """
        Prétraitement et détection des contours avec Canny.
        
        Args:
            img: Image d'entrée.
            minVal: Seuil minimum pour Canny.
            maxVal: Seuil maximum pour Canny.
        
        Returns:
            Image des contours détectés.
        """
        # Redimensionner tout en gardant le ratio
        img_resized = self.resize_keep_ratio(img)
        
        # Convertir en niveaux de gris
        img = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

        # Appliquer un filtre bilatéral et un seuillage adaptatif
        img = cv2.bilateralFilter(img, 9, 75, 75)
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 115, 4)

        # Flou médian
        img = cv2.medianBlur(img, 11)

        # Ajout d'une bordure noire
        img = cv2.copyMakeBorder(img, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=[0, 0, 0])

        # Détection des contours avec Canny
        edges = cv2.Canny(img, minVal, maxVal)

        # Fermer les gaps entre les bords
        closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 11)))
        return closed_edges

    def findPageContours(self, closedEdges, img):
        """
        Trouver un contour de page avec exactement 4 points.
        
        Args:
            closedEdges: Image des contours fermés.
            img: Image d'origine (pour référence).
        
        Returns:
            Contour de la page (4 points) ou None si aucun contour n'est trouvé.
        """
        if len(closedEdges.shape) != 2:
            raise ValueError("closedEdges doit être une image 2D (binaire).")

        contours, _ = cv2.findContours(closedEdges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            return None

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
            perimeter = cv2.arcLength(cnt, True)
            epsilon = 0.01 * perimeter
            while epsilon < 0.1 * perimeter:
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    return approx
                epsilon += 0.01 * perimeter
        
        print("Aucun contour avec exactement 4 points n'a été trouvé.")
        return None

    def perspImageTransform(self, img, sPoints):
        """
        Transforme la perspective à partir des points sources vers les points cibles.
        
        Args:
            img: Image d'entrée.
            sPoints: Points sources (4 points).
        
        Returns:
            Image transformée.
        """
        height = max(np.linalg.norm(sPoints[0] - sPoints[1]),
                     np.linalg.norm(sPoints[2] - sPoints[3]))
        width = max(np.linalg.norm(sPoints[1] - sPoints[2]),
                    np.linalg.norm(sPoints[3] - sPoints[0]))

        tPoints = np.array([[0, 0], [0, height], [width, height], [width, 0]], dtype=np.float32)

        if sPoints.dtype != np.float32:
            sPoints = sPoints.astype(np.float32)

        M = cv2.getPerspectiveTransform(sPoints, tPoints)
        transformed_image = cv2.warpPerspective(img, M, (int(width), int(height)))
        return transformed_image

    def improve_image(self, img):
        """
        Améliore l'image avec Albumentations.
        
        Args:
            img: Image d'entrée.
        
        Returns:
            Image améliorée.
        """
        transform = A.Compose([
            A.GaussianBlur(blur_limit=(1, 3), p=0.2),
            A.RandomBrightnessContrast(brightness_limit=0.4, contrast_limit=0.5, p=0.7),
            A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=20, val_shift_limit=50, p=0.6),
            A.CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), p=0.6),
            A.ImageCompression(quality_lower=100, p=0.3),
        ])
        augmented = transform(image=img)
        return augmented['image']

    def convert_to_grayscale(self, img):
        """
        Convertir l'image en niveaux de gris.
        
        Args:
            img: Image d'entrée.
        
        Returns:
            Image en niveaux de gris.
        """
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def resize_to_standard_size(self, img, class_name="autre"):
        """
        Redimensionne l'image à la taille standard exacte (largeur et hauteur) de la classe.
        
        Args:
            img: Image à redimensionner (numpy array).
            class_name: Classe de l'image ("BS", "ordonnance", "facture", ou "autre").
        
        Returns:
            Image redimensionnée à la taille standard.
        """
        standard_size = self.standard_sizes.get(class_name, self.standard_sizes["autre"])
        target_width, target_height = standard_size
        return cv2.resize(img, (target_width, target_height))

    def preprocess_image(self, image, closedEdges, class_name="autre"):
        """
        Pipeline complet de prétraitement.
        
        Args:
            image: Image d'entrée (numpy array).
            closedEdges: Image des contours fermés (numpy array).
            class_name: Classe de l'image ("BS", "ordonnance", "facture", ou "autre").
        
        Returns:
            Image prétraitée (en niveaux de gris, à la taille standard).
        """
        # Vérification de l'image
        if image is None:
            print("Erreur : Impossible de charger l'image !")
            return None

        print("Image chargée avec succès.")

        # Étape 1 : Redimensionner l'image en gardant le ratio (basé sur la largeur cible de la classe)
        resized_image = self.resize_keep_ratio(image, class_name=class_name)

        # Étape 2 : Vérifier `closedEdges`
        if closedEdges is None or np.count_nonzero(closedEdges) == 0:
            print("Erreur : closedEdges est vide ou n'a pas de contours !")
            # Redimensionner à la taille standard avant de retourner
            return self.resize_to_standard_size(resized_image, class_name=class_name)

        print("closedEdges contient des contours.")
        print("Dimensions de closedEdges :", closedEdges.shape)

        # Étape 3 : Trouver les contours de la page
        if closedEdges is not None and len(closedEdges.shape) == 2:
            page_contour = self.findPageContours(closedEdges, resized_image)
        else:
            print("Erreur : closedEdges n'est pas une image 2D valide.")
            page_contour = None

        # Étape 4 : Vérifier `pageContour`
        if page_contour is None or len(page_contour) == 0:
            print("Erreur : Aucun contour trouvé !")
            # Redimensionner à la taille standard avant de retourner
            return self.resize_to_standard_size(resized_image, class_name=class_name)

        print("Contours trouvés (4 points) :", page_contour)

        # Étape 5 : Appliquer la transformation de perspective pour recadrer
        sPoints = page_contour.squeeze()
        cropped_image = self.perspImageTransform(resized_image, sPoints)

        # Étape 6 : Améliorer l'image
        improved_image = self.improve_image(cropped_image)

        # Étape 7 : Convertir en niveaux de gris
        grayscale_image = self.convert_to_grayscale(improved_image)

        # Étape 8 : Convertir l'image en niveaux de gris (1 canal) en image BGR (3 canaux)
        final_image = cv2.cvtColor(grayscale_image, cv2.COLOR_GRAY2BGR)

        # Étape 9 : Redimensionner à la taille standard exacte (largeur et hauteur)
        final_image = self.resize_to_standard_size(final_image, class_name=class_name)

        return final_image