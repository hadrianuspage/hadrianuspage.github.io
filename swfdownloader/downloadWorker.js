self.onmessage = function(e) {
    const { fileType, start, end } = e.data;
    const JSZip = require('jszip'); // Make sure to include JSZip in your worker context
    const zip = new JSZip();
    let downloadedFiles = 0;
    let failedFiles = 0;

    const downloadFile = (index) => {
        return new Promise((resolve) => {
            const paddedIndex = String(index).padStart(2, '0');
            let url = '';

            // Construct the URL based on fileType
            // (You can copy the URL logic from your original code here)

            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        failedFiles++;
                        throw new Error('Network response was not ok');
                    }
                    return response.blob();
                })
                .then(blob => {
                    zip.file(`${fileType}/${url.split('/').pop()}`, blob);
                    downloadedFiles++;
                    resolve();
                })
                .catch(() => {
                    failedFiles++;
                    resolve();
                });
        });
    };

    const downloadFiles = async () => {
        for (let i = start; i <= end; i++) {
            await downloadFile(i);
            self.postMessage({ downloadedFiles, failedFiles });
        }
        const content = await zip.generateAsync({ type: 'blob' });
        self.postMessage({ content, downloadedFiles, failedFiles });
    };

    downloadFiles();
};
