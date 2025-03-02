self.onmessage = function (e) {
    const { fileType, start, end } = e.data;
    const zip = new JSZip();
    let downloadedFiles = 0;
    let failedFiles = 0;

    const downloadFile = (index) => {
        return new Promise((resolve) => {
            const paddedIndex = String(index).padStart(2, '0');
            let url;

            // Construct the URL based on fileType
            if (fileType === 'enemies') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/enemies_v2/ene_${paddedIndex}.swf`;
            } else if (fileType === 'enemiesv2') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/enemies_v2/ene_${paddedIndex}_v2.swf`;
            } else if (fileType === 'enemiesv3') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/enemies_v2/ene_${paddedIndex}_v3.swf`;
            } else if (fileType === 'backitems') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/back_${paddedIndex}.swf`;
            } else if (fileType === 'malehairs') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/hair_${paddedIndex}_0.swf`;
            } else if (fileType === 'girlhairs') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/hair_${paddedIndex}_1.swf`;
            } else if (fileType === 'malesets') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/set_${paddedIndex}_0.swf`;
            } else if (fileType === 'girlsets') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/set_${paddedIndex}_1.swf`;
            } else if (fileType === 'weapons') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/items/wpn_${paddedIndex}.swf`;
            } else if (fileType === 'pets') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/pets/pet_${paddedIndex}.swf`;
            } else if (fileType === 'petsv2') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/pets/pet_${paddedIndex}_v2.swf`;
            } else if (fileType === 'petsv3') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/pets/pet_${paddedIndex}_v3.swf`;
            } else if (fileType === 'skills') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/skills_v2/skill_${paddedIndex}.swf`;
            } else if (fileType === 'skillsv2') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/skills_v2/skill_${paddedIndex}_v2.swf`;
            } else if (fileType === 'skillsv3') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/skills_v2/skill_${paddedIndex}_v3.swf`;
            } else if (fileType === 'moveskills') {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/skills_v2/move_${paddedIndex}.swf`;
            } else {
                url = `https://shinobiwarfare.fra1.cdn.digitaloceanspaces.com/data/swf/skills_v2/sen_${paddedIndex}.swf`;
            }

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
                    self.postMessage({ downloadedFiles, failedFiles });
                })
                .catch(() => {
                    failedFiles++;
                    self.postMessage({ downloadedFiles, failedFiles });
                });
        });
    };

    const downloadFiles = async () => {
        for (let i = start; i <= end; i++) {
            await downloadFile(i);
        }
        const content = await zip.generateAsync({ type: 'blob' });
        self.postMessage({ content, downloadedFiles, failedFiles });
    };

    downloadFiles();
};
