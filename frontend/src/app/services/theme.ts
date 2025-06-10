export const getDarkModeSelector = (): string | boolean => {
    const savedTheme = localStorage.getItem('user-theme');
  
    // Si 'dark' ou 'light' est stocké, utiliser `.dark-mode` ou désactiver
    if (savedTheme === 'dark') return true;
    if (savedTheme === 'light') return false;
  
    // Par défaut, suivre le système avec 'media'
    return 'system'; // ou 'none' pour désactiver complètement
  };