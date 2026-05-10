/**
 * BildungsRadar - Frontend JavaScript
 * Handhabt Filter, KI-Analyse und Vergleichsfunktion.
 */

// --- Filter-Buttons sind <a>-Links: Server filtert per ?type= URL-Parameter
// Kein zusaetzliches Frontend-Filter-JS noetig, weil der Server schon nur die
// passenden Einrichtungen sendet. Die Active-Klasse wird vom Template gesetzt.
//


// --- KI-Analyse starten ---
function analyzeInstitution(institutionId, button) {
    button.disabled = true;
    button.textContent = "Analysiere...";

    // Prompt-Version und Temperature aus den Dropdowns lesen
    var promptSelect = document.getElementById("prompt-" + institutionId);
    var tempSelect = document.getElementById("temp-" + institutionId);
    var promptVersion = promptSelect ? promptSelect.value : "v2";
    var temperature = tempSelect ? parseFloat(tempSelect.value) : 0.3;

    var analysisDiv = document.getElementById("analysis-" + institutionId);
    analysisDiv.innerHTML = '<p class="analysis-loading">KI analysiert...</p>';

    fetch("/api/analyze/" + institutionId, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            prompt_version: promptVersion,
            temperature: temperature
        })
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                var analysis = data.analysis;
                var html = '<div class="analysis-result">';
                html += "<h4>KI-Analyse</h4>";
                html += "<p><strong>Zusammenfassung:</strong> " + analysis.summary + "</p>";

                // Preise: kann String ODER Objekt sein
                if (analysis.prices && typeof analysis.prices === "object" && !Array.isArray(analysis.prices)) {
                    html += '<div><strong>Preise:</strong><ul style="margin:4px 0 4px 20px;">';
                    Object.keys(analysis.prices).forEach(function (key) {
                        html += "<li><strong>" + key + ":</strong> " + analysis.prices[key] + "</li>";
                    });
                    html += "</ul></div>";
                } else {
                    html += "<p><strong>Preise:</strong> " + (analysis.prices || "Keine Angabe") + "</p>";
                }

                if (analysis.offerings && analysis.offerings.length > 0) {
                    html += "<p><strong>Angebote:</strong> " + analysis.offerings.join(", ") + "</p>";
                }
                if (analysis.specializations && analysis.specializations.length > 0) {
                    html += "<p><strong>Spezialisierungen:</strong> " + analysis.specializations.join(", ") + "</p>";
                }

                html += "</div>";
                analysisDiv.innerHTML = html;
                button.textContent = "Erneut analysieren";
                button.disabled = false;
            } else {
                analysisDiv.innerHTML = '<p class="analysis-loading">Fehler bei der Analyse.</p>';
                button.textContent = "Erneut versuchen";
                button.disabled = false;
            }
        })
        .catch(function (error) {
            console.error("Analyse-Fehler:", error);
            analysisDiv.innerHTML = '<p class="analysis-loading">Fehler bei der Analyse.</p>';
            button.textContent = "Erneut versuchen";
            button.disabled = false;
        });
}


// --- Vergleichs-Funktion ---
function updateCompare() {
    var checkboxes = document.querySelectorAll('.compare-checkbox input:checked');
    var compareBar = document.getElementById("compare-bar");
    var compareCount = document.getElementById("compare-count");

    if (checkboxes.length > 0) {
        compareBar.style.display = "flex";
        compareCount.textContent = checkboxes.length;
    } else {
        compareBar.style.display = "none";
    }
}

function openCompare() {
    var checkboxes = document.querySelectorAll('.compare-checkbox input:checked');
    var ids = [];
    checkboxes.forEach(function (cb) { ids.push(cb.value); });

    if (ids.length > 0) {
        window.location.href = "/compare?ids=" + ids.join(",");
    }
}


// --- Google Bewertungen laden ---
function loadGoogleRatings(searchId, typeFilter) {
    var buttons = document.querySelectorAll(".btn-ratings");
    var status = document.getElementById("rating-status");

    buttons.forEach(function(b) { b.disabled = true; });
    status.textContent = "Lade Bewertungen... Bitte warten...";
    status.style.color = "#3498db";

    fetch("/api/fetch-ratings/" + searchId, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({filter: typeFilter, max: 50})
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                status.textContent = data.message;
                status.style.color = "#27ae60";
                // Seite nach 2 Sekunden neu laden um Sterne anzuzeigen
                setTimeout(function() {
                    window.location.reload();
                }, 2000);
            } else {
                status.textContent = data.error || "Fehler beim Laden der Bewertungen";
                status.style.color = "#e74c3c";
                buttons.forEach(function(b) { b.disabled = false; });
            }
        })
        .catch(function (error) {
            console.error("Rating-Fehler:", error);
            status.textContent = "Fehler: " + error.message;
            status.style.color = "#e74c3c";
            buttons.forEach(function(b) { b.disabled = false; });
        });
}


// --- Favoriten-Funktion ---
function toggleFavorite(institutionId, button) {
    fetch("/api/favorite/" + institutionId, { method: "POST" })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                if (data.is_favorite) {
                    button.classList.add("active");
                    button.innerHTML = "&#9829;";
                    button.title = "Favorit entfernen";
                } else {
                    button.classList.remove("active");
                    button.innerHTML = "&#9825;";
                    button.title = "Favorit";
                    // Auf der Favoriten-Seite: Karte ausblenden
                    var card = button.closest(".institution-card");
                    if (card && window.location.pathname === "/favorites") {
                        card.style.opacity = "0.3";
                    }
                }
            }
        })
        .catch(function (error) {
            console.error("Favoriten-Fehler:", error);
        });
}
