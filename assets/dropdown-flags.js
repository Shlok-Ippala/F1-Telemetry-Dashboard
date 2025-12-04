// Inject flag icons into Mantine Select dropdown options
// This script observes the DOM for Mantine dropdown options and adds flag images

const FLAG_ICONS = {
    'bahrain': 'bh',
    'saudi': 'sa',
    'jeddah': 'sa',
    'australia': 'au',
    'australian': 'au',
    'melbourne': 'au',
    'japan': 'jp',
    'japanese': 'jp',
    'suzuka': 'jp',
    'china': 'cn',
    'chinese': 'cn',
    'shanghai': 'cn',
    'miami': 'us',
    'emilia': 'it',
    'imola': 'it',
    'monaco': 'mc',
    'canada': 'ca',
    'canadian': 'ca',
    'montreal': 'ca',
    'spain': 'es',
    'spanish': 'es',
    'barcelona': 'es',
    'austria': 'at',
    'austrian': 'at',
    'spielberg': 'at',
    'britain': 'gb',
    'british': 'gb',
    'silverstone': 'gb',
    'hungary': 'hu',
    'hungarian': 'hu',
    'budapest': 'hu',
    'hungaroring': 'hu',
    'belgium': 'be',
    'belgian': 'be',
    'spa': 'be',
    'netherlands': 'nl',
    'dutch': 'nl',
    'zandvoort': 'nl',
    'italy': 'it',
    'italian': 'it',
    'monza': 'it',
    'azerbaijan': 'az',
    'baku': 'az',
    'singapore': 'sg',
    'marina bay': 'sg',
    'united states': 'us',
    'austin': 'us',
    'cota': 'us',
    'americas': 'us',
    'mexico': 'mx',
    'mexican': 'mx',
    'brazilian': 'br',
    'brazil': 'br',
    'sao paulo': 'br',
    'são paulo': 'br',
    'paulo': 'br',
    'interlagos': 'br',
    'las vegas': 'us',
    'vegas': 'us',
    'qatar': 'qa',
    'losail': 'qa',
    'abu dhabi': 'ae',
    'yas marina': 'ae',
    'portugal': 'pt',
    'portuguese': 'pt',
    'portimao': 'pt',
    'turkey': 'tr',
    'turkish': 'tr',
    'istanbul': 'tr',
    'styria': 'at',
    'styrian': 'at',
    'eifel': 'de',
    'nurburgring': 'de',
    'russia': 'ru',
    'russian': 'ru',
    'sochi': 'ru',
    'tuscany': 'it',
    'tuscan': 'it',
    'mugello': 'it',
    'sakhir': 'bh',
    'france': 'fr',
    'french': 'fr',
    'paul ricard': 'fr',
    'korean': 'kr',
    'korea': 'kr',
    'indian': 'in',
    'india': 'in',
    'german': 'de',
    'germany': 'de',
    'hockenheim': 'de',
    'malaysian': 'my',
    'malaysia': 'my',
    'sepang': 'my',
    'pre-season': 'bh',
    'testing': 'bh',
};

function getCountryCode(raceName) {
    const lower = raceName.toLowerCase();
    for (const [keyword, code] of Object.entries(FLAG_ICONS)) {
        if (lower.includes(keyword)) {
            return code;
        }
    }
    return 'xx'; // Default unknown
}

function createFlagElement(countryCode) {
    const img = document.createElement('img');
    img.src = `https://flagcdn.com/w20/${countryCode}.png`;
    img.srcset = `https://flagcdn.com/w40/${countryCode}.png 2x`;
    img.width = 20;
    img.height = 15;
    img.alt = countryCode.toUpperCase();
    img.style.marginRight = '8px';
    img.style.borderRadius = '2px';
    img.style.verticalAlign = 'middle';
    return img;
}

function addFlagsToOptions() {
    // Find all Mantine Select options that don't already have flags
    const options = document.querySelectorAll('.mantine-Select-option:not([data-flag-added])');
    
    options.forEach(option => {
        const text = option.textContent.trim();
        if (text && text.length > 0) {
            const countryCode = getCountryCode(text);
            if (countryCode) {
                const flag = createFlagElement(countryCode);
                option.insertBefore(flag, option.firstChild);
                option.setAttribute('data-flag-added', 'true');
                option.style.display = 'flex';
                option.style.alignItems = 'center';
            }
        }
    });
}

// Observe DOM changes to add flags when dropdowns open
const observer = new MutationObserver((mutations) => {
    let shouldAddFlags = false;
    
    mutations.forEach((mutation) => {
        if (mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1) { // Element node
                    if (node.classList && (
                        node.classList.contains('mantine-Select-dropdown') ||
                        node.classList.contains('mantine-Select-option') ||
                        node.querySelector && node.querySelector('.mantine-Select-option')
                    )) {
                        shouldAddFlags = true;
                    }
                }
            });
        }
    });
    
    if (shouldAddFlags) {
        setTimeout(addFlagsToOptions, 10);
    }
});

// Start observing
document.addEventListener('DOMContentLoaded', () => {
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

