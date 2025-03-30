github:@RayenR1 | linkedin :Rayen Jlassi
this service is done By *Rayen Jlassi for alomost the entire work & Skander kammoun for keywords 2 nootebook* 
# Layout Detection Service

## Description
Ce service détecte les layouts (tableaux, texte tapé, texte manuscrit) des images consommées à partir des topics Kafka `filtered-BS`, `filtered-ordonnances`, `filtered-facture`, et `filtered-autre`. Il utilise MLflow pour le suivi des métriques de segmentation et envoie les résultats (image et JSON) au topic `output-layout`.

## Prérequis
- Docker
- Docker Compose
- Python 3.10.16

## Installation
1. Clonez le dépôt ou créez la structure suivante :