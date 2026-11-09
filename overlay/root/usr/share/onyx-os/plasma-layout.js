// ONYX OS 0.3 native Plasma layout. Build the new panel BEFORE deleting
// the existing panels, so a failed widget creation does not leave a blank desktop.
var dock = new Panel();
dock.location = "bottom";
dock.height = 54;
dock.floating = true;
dock.hiding = "none";
dock.addWidget("org.kde.plasma.kickoff");
dock.addWidget("org.kde.plasma.icontasks");
dock.addWidget("org.kde.plasma.systemtray");
dock.addWidget("org.kde.plasma.digitalclock");
dock.floating = true;
// Remove previous panels only after the replacement has been constructed.
var oldPanels = panels();
for (var i = oldPanels.length - 1; i >= 0; --i) {
    if (oldPanels[i].id !== dock.id) oldPanels[i].remove();
}
