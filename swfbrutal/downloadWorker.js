// downloadWorker.js
self.onmessage = function(e) {
    const { fileType, start, end } = e.data;
    const zip = new JSZip();
    let downloadedFiles = 0;
    let failedFiles = 0;

    const downloadFile = (index) => {
        return new Promise((resolve) => {
            const paddedIndex = String(index).padStart(2, '0');
            let url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/${fileType}/file_${paddedIndex}.swf`;

            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        failedFiles++;
                        throw new Error('Network response was not ok');
                    }
                    return response.blob();
                })
                .then(blob => {
                    zip.file(`file_${paddedIndex}.swf`, blob);
                    downloadedFiles++;
                    resolve();
                })
                .catch(() => {
                    failedFiles++;
                    resolve();
                });
        });
    };

    const processBatch = async (start, end) => {
        for (let i = start; i <= end; i++) {
            await downloadFile(i);
            self.postMessage({ downloadedFiles, failedFiles });
        }
        const content = await zip.generateAsync({ type: 'blob' });
        self.postMessage({ content });
    };

    processBatch(start, end);
};
