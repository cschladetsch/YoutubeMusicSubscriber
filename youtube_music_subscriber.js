
// YouTube Music Artist Subscriber
// Paste this in browser console on music.youtube.com

const artists = [
    "Gramatik",
    "Too Many Zooz",
    "Funky Destination",
    "Meute",
    "Opiuo",
    "Parov Stelar",
    "Otyken",
    "Adhesive Wombat",
    "Rammstein",
    "Odd Chap",
    "Stupid Human",
    "Caravan Palace",
    "Ice Paper",
    "Phoenix Legend",
    "The Hu",
    "Ummet Ozcan",
];

let currentIndex = 0;

function subscribeNext() {
    if (currentIndex >= artists.length) {
        console.log("✅ All artists processed!");
        return;
    }
    
    const artist = artists[currentIndex++];
    console.log(`🎵 Processing ${currentIndex}/${artists.length}: ${artist}`);
    
    // Open search in current tab
    const searchUrl = `https://music.youtube.com/search?q=${encodeURIComponent(artist + " music")}`;
    window.location.href = searchUrl;
    
    // Wait for user to subscribe, then continue
    console.log("👆 Click Subscribe button, then run subscribeNext() to continue");
}

// Auto-continue version (opens new tabs)
function subscribeAll() {
    artists.forEach((artist, index) => {
        setTimeout(() => {
            console.log(`🎵 Opening: ${artist}`);
            window.open(`https://music.youtube.com/search?q=${encodeURIComponent(artist)}`, '_blank');
        }, index * 2000); // 2 second delay between opens
    });
}

console.log("🎵 YouTube Music Artist Subscriber Ready!");
console.log("Commands:");
console.log("  subscribeNext() - Process one artist at a time");
console.log("  subscribeAll()  - Open all artists in new tabs");
console.log("");
console.log("Starting with first artist...");
subscribeNext();
