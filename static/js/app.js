/**
 * BildungsRadar - Frontend JavaScript
 * Handhabt Filter, KI-Analyse und Vergleichsfunktion.
 */

// --- Filter-Funktion ---
// Zeigt/versteckt Einrichtungen nach Kategorie
document.addEventListener("DOMContentLoaded", function () {
    var filterButtons = document.querySelectorAll(".filter-btn");

    filterButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            var filterType = this.getAttribute("data-filter");

            // Aktiven Button markieren
            filterButtons.forEach(function (b) { b.classList.remove("active"); });
            this.classList.add("active");

            // Karten filtern
            var cards = document.querySelectorAll(".institution-card");
            cards.forEach(function (card) {
                if (filterType === "all" || card.getAttribute("data-type") === filterType) {
                    card.classList.remove("hidden");
                } else {
                    card.classList.add("hidden");
                }
            });
        });
    });
});


// --- KI-Analyse starten ---
function analyzeInstitution(institutionId, button) {
    button.disabled = true;
    button.textContent = "Analysiere...";

    var analysisDiv = document.getElementById("analysis-" + institutionId);
    analysisDiv.innerHTML = '<p class="analysis-loading">KI analysiert die Webseite...</p>';

    fetch("/api/analyze/" + institutionId, { method: "POST" })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.success) {
                var analysis = data.analysis;
                var html = '<div class="analysis-result">';
                html += "<h4>KI-Analyse</h4>";
                html += "<p><strong>Zusammenfassung:</strong> " + analysis.summary + "</p>";
                html += "<p><strong>Preise:</strong> " + analysis.prices + "</p>";

                if (analysis.offerings && analysis.offerings.length > 0) {
                    html += "<p><strong>Angebote:</strong> " + analysis.offerings.join(", ") + "</p>";
                }
                if (analysis.specializations && analysis.specializations.length > 0) {
                    html += "<p><strong>Spezialisierungen:</strong> " + analysis.specializations.join(", ") + "</p>";
                }

                html += "</div>";
                analysisDiv.innerHTML = html;
                button.textContent = "Analysiert";
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
