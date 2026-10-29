// JoeSpeaking.com homepage card: flat amber background, so plate "fill" is clean.
window.OG = {
  image: "card.jpg", width: 1200, height: 630, loop: 4.0,
  plate: { mode: "fill" },
  layers: [
    { id: "badge",   box: [45, 38, 442, 99],   role: "pop" },
    { id: "line1",   box: [50, 150, 445, 62],  role: "rise" },
    { id: "line2",   box: [50, 212, 642, 74],  role: "rise" },
    { id: "orb",     box: [52, 315, 192, 192], role: "spin" },
    { id: "arrow",   box: [250, 300, 474, 150], role: "wipe" },
    { id: "report",  box: [724, 38, 463, 505], role: "stamp" },
    { id: "logo",    box: [45, 521, 330, 71],  role: "slide" }
  ]
};
