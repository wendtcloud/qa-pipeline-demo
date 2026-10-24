export function validateItem(body) {
    const errors = [];
    if (typeof body !== "object" || body === null || Array.isArray(body)) {
        return ["body must be a JSON object"];
    }

    const { name, sku, quantity, price } = body;

    if (typeof name !== "string" || name.trim().length < 1 || name.trim().length > 50)
        errors.push("name must be a string of 1-50 characters");

    if (typeof sku !== "string" || !/^[A-Z0-9-]{3,20}$/.test(sku))
        errors.push("sku must be 3-20 characters: A-Z, 0-9, hyphen");

    if (!Number.isInteger(quantity) || quantity < 0 || quantity > 1000)
        errors.push("quantity must be an integer between 0 and 1000");

    if (typeof price !== "number" || !Number.isFinite(price) || price < 0 || price > 100000)
        errors.push("price must be a number between 0 and 100000");

    return errors;
}