// Define functions in global scope
function roundUncertainty(uncertainty) {
    if (uncertainty === null || uncertainty === undefined || uncertainty === 0) {
        return "";
    }

    // order of magnitude of the uncertainty
    const magnitude = Math.floor(Math.log10(uncertainty));
    const firstDigit = uncertainty / Math.pow(10, magnitude);

    // Use 2 significant figures for values starting with 1 or 2, otherwise use 1
    const sigFigs = firstDigit < 3 ? 2 : 1;

    const uncertaintyStr = uncertainty.toString();
    if (uncertaintyStr.replace(/^0\./, '').length <= sigFigs) {
        return uncertaintyStr;
    }

    const scale = Math.pow(10, sigFigs - magnitude - 1);
    return (Math.round(uncertainty * scale) / scale).toString();
}

function roundMagnitude(value, uncertainty) {
    if (value === null || value === undefined) return "N/A";
    if (uncertainty === 0 || uncertainty === "") return value.toString();

    // get number of decimal places in uncertainty
    const uncertaintyStr = uncertainty.toString();
    const uncertaintyDecimalPlaces = (uncertaintyStr.split('.')[1] || '').length;

    // get the decimal places in the original value
    const valueDecimalPlaces = (value.toString().split('.')[1] || '').length;

    // use at least one decimal place for uncertainties between 0.1 and 1
    const minDecimalPlaces = (uncertainty >= 0.1 && uncertainty < 1) ? 1 : 0;

    // confirm correct precision
    const finalDecimalPlaces = Math.max(
        minDecimalPlaces,
        Math.min(uncertaintyDecimalPlaces, valueDecimalPlaces)
    );
    return value.toFixed(finalDecimalPlaces);
}

// Also make them available on window for consistency
window.NumberFormatting = {
    roundUncertainty,
    roundMagnitude
};
