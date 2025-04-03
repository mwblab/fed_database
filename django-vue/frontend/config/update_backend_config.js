const fs = require('fs');
const readline = require('readline');

const path1 = '../src/components/Edit.vue';
const path2 = '../src/components/Studies.vue'
const oldIP = '128.173.224.170'; // IP to replace
const ipRegex = new RegExp(`\\b${oldIP}\\b`, 'g'); // Regex to match the specific IP

const rl = readline.createInterface({
	  input: process.stdin,
	  output: process.stdout
});


rl.question('Enter the new backend IP address: ', (newIP) => {
    if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(newIP)) {
        console.error('❌ Invalid IP address format.');
	rl.close();
	return;
    }

    readUpdateFile(path1, newIP);
    readUpdateFile(path2, newIP);
});


function readUpdateFile(path, newIP) {

    fs.readFile(path, 'utf8', (err, data) => {
	if (err) {
            console.error(`❌ Error reading file: ${err}`);
            rl.close(); 
	    return;
        }

	const updatedData = data.replace(ipRegex, newIP);

        fs.writeFile(path, updatedData, 'utf8', (err) => {
	if (err) {
            console.error(`❌ Error writing file: ${err}`);
        } else {
            console.log(`✅ Successfully update new backend IP ${newIP}`);
        }
        rl.close();
	});
    });

}

