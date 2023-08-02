const REGISTRY_URL = "/registry.json";

// utils =======================================================================

function makeDiv(cls, children) {
    const div = document.createElement('div');
    div.classList.add(cls);

    if (typeof children !== 'undefined') {
        div.append(...children);
    }

    return div;
}

function makeSpan(cls, text) {
    const span = document.createElement('span');
    span.classList.add(cls);

    span.innerText = text;

    return span;
}

function errorDiv(msg) {
    const div = makeDiv('error');
    div.innerText = `error: ${msg}`;

    return div;
}

// rendering ===================================================================

function renderDoc(text) {
    const el = document.createElement('pre');
    el.classList.add('doc');
    el.innerText = text;

    return el;
}

function renderSig(declwith, name, sig) {
    const kids = [
        makeSpan('none', declwith + ' '),
        makeSpan('var', name),
        makeSpan('none', '('),
    ];

    sig.params.forEach(({ name, kind, anno }, i) => {
        if (i > 0) {
            kids.push(makeSpan('none', ', '));
        }

        // param name
        let paramName = '';

        switch (kind) {
            case 'keyword_only':
            case 'positional_or_keyword':
                paramName = name;
                break;
            default:
                paramName = `<uh oh this is a ${kind} parameter>`;
                break;
        }

        kids.push(makeSpan('none', paramName));

        if (anno) {
            kids.push(makeSpan('none', ': '));
            kids.push(makeSpan('type', anno));
        }
    });

    kids.push(makeSpan('none', ')'));

    if (sig.returns) {
        kids.push(makeSpan('none', ' -> '));
        kids.push(makeSpan('type', sig.returns));
    }

    return makeDiv('decl', kids);
}

function renderFunction({ name, sig, doc }) {
    const kids = [];

    kids.push(renderSig('def', name, sig));
    if (doc) kids.push(renderDoc(doc));

    return makeDiv('function', kids);
}

function renderClass({ name, sig, doc, classes, functions }) {
    const kids = [];

    kids.push(renderSig('class', name, sig));
    if (doc) kids.push(renderDoc(doc));

    classes.forEach((meta) => {
        kids.push(renderClass(meta));
    });

    functions.forEach((meta) => {
        kids.push(renderFunction(meta));
    });

    return makeDiv('class', kids);
}

function renderModule({ name, doc, classes, functions }) {
    const kids = [];

    kids.push(makeDiv('decl', [
        makeSpan('none', name),
    ]));

    if (doc) kids.push(renderDoc(doc));

    classes.forEach((meta) => {
        kids.push(renderClass(meta));
    });

    functions.forEach((meta) => {
        kids.push(renderFunction(meta));
    });

    return makeDiv('module', kids);
}

// =============================================================================

/** returns loaded json, or null if not found */
async function fetchRegistry() {
    const res = await fetch(REGISTRY_URL);
    if (!res.ok) return null;

    return await res.json();
}

/**
 * returns an html div that represents a documented registry. errors are
 * handled by creating 
 */
export default async function gdoc() {
    const reg = await fetchRegistry();
    if (!reg) return errorDiv(`couldn't fetch registry at ${REGISTRY_URL}`);

    const modules = reg.modules.map((m) => renderModule(m));
    return makeDiv('gdoc', modules);
}
