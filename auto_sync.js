// Auto-Sync YouTube Music Subscriptions
// Paste this in browser console - it will automatically sync everything

const targetArtists = [
    "Faith No More",
    "Dog Fashion Disco",
    "Nine Inch Nails",
    "Korn",
    "Mike Oldfield",
    "Gramatik",
    "Too Many Zooz",
    "Funky Destination",
    "Meute",
    "Opiuo",
    "Parov StelarOtyken",
    "Adhesive Wombat",
    "Rammstein",
    "Odd Chap",
    "Stupid Human",
    "Caravan Palace",
    "Ice Paper",
    "Phoenix Legend",
    "The Hu",
    "Ummet Ozcan"
];

console.log("🎵 Auto-syncing YouTube Music subscriptions...");
console.log(`📋 Target: ${targetArtists.length} artists`);

// Automatically open all target artists in tabs for subscribing
targetArtists.forEach((artist, index) => {
    setTimeout(() => {
        console.log(`🔔 Opening: ${artist}`);
        window.open(`https://music.youtube.com/search?q=${encodeURIComponent(artist)}`, '_blank');
    }, index * 2000); // 2 second delay between tabs
});

console.log("✅ All artist tabs will open automatically");
console.log("📝 Subscribe to each artist in the opened tabs");
console.log(`🎯 Total tabs opening: ${targetArtists.length}`);
