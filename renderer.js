import { addMarker } from './mapUtils.js';

window.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('upload-button');

    
    // Initialize your Leaflet map here
    const map = L.map('map').setView([51.505, -0.09], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    addMarker(map, 51.505, -0.09);

  
    uploadButton.addEventListener('click', () => {
      window.electron.invoke('show-open-dialog').then((result) => {
        if (!result.canceled) {
          const filePath = result.filePaths[0];
          window.electron.invoke('read-file', filePath).then((data) => {
            console.log('File content received in renderer:', data);
            // Process the file content and use it in your Leaflet map

          });
        }
      });
    });
    

  });
  
 