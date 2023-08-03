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

function renderModuleSig(name, uname) {
    const div = makeDiv('decl', [
        makeSpan('none', name),
    ]);

    if (typeof uname !== 'undefined') {
        div.id = uname;
    }

    return div;
}

/** renders sig. set uname to make this div jumpable */
function renderSig(declwith, name, sig, uname) {
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

    const div = makeDiv('decl', kids);
    if (typeof uname !== 'undefined') {
        div.id = uname;
    }

    return div;
}

function renderFunction({ name, uname, sig, doc }) {
    const kids = [];

    kids.push(renderSig('def', name, sig, uname));
    kids.push(renderSig('def', name, sig, uname));
    if (doc) kids.push(renderDoc(doc));

    return makeDiv('function', kids);
}

function renderClass({ name, uname, sig, doc, classes, functions }) {
    const kids = [];

    kids.push(renderSig('class', name, sig, uname));
    if (doc) kids.push(renderDoc(doc));

    classes.forEach((meta) => {
        kids.push(renderClass(meta));
    });

    functions.forEach((meta) => {
        kids.push(renderFunction(meta));
    });

    return makeDiv('class', kids);
}

function renderModule({ name, uname, doc, classes, functions }) {
    const kids = [];

    kids.push(renderModuleSig(name, uname));
    if (doc) kids.push(renderDoc(doc));

    classes.forEach((meta) => {
        kids.push(renderClass(meta));
    });

    functions.forEach((meta) => {
        kids.push(renderFunction(meta));
    });

    return makeDiv('module', kids);
}

// sidebar index ===============================================================

function makeIndexNode(decl, kids) {
    return makeDiv('index-node', [decl, ...kids]);
}

function renderIndexedDecl(declwith, name, sig, uname, kids) {
    const decl = renderSig(declwith, name, sig);
    decl.addEventListener('click', () => {
        window.location.hash = uname;
    });

    return makeIndexNode(decl, kids)
}

function renderIndexedFunction({ name, sig, uname}) {
    return renderIndexedDecl('def', name, sig, uname, []);
}

function renderIndexedClass({ name, sig, uname, functions, classes }) {
    const iFunctions = functions.map(renderIndexedFunction);
    const iClasses = classes.map(renderIndexedClass);
    const kids = iFunctions.concat(iClasses);

    return renderIndexedDecl('class', name, sig, uname, kids);
}

function renderIndexedModule({ name, uname, functions, classes }) {
    const decl = renderModuleSig(name);
    decl.addEventListener('click', () => {
        window.location.hash = uname;
    })

    const iFunctions = functions.map(renderIndexedFunction);
    const iClasses = classes.map(renderIndexedClass);
    const kids = iFunctions.concat(iClasses);

    return makeIndexNode(decl, kids);
}

function renderIndex(registry) {
    return makeDiv('index', registry.modules.map(renderIndexedModule));
}

// =============================================================================

/** used to create unique registry ids */
const UNAMES = new Set();

/** returns loaded json, or null if not found */
async function fetchRegistry() {
    const res = await fetch(REGISTRY_URL);
    if (!res.ok) return null;

    return await res.json();
}

/** adds a 'uname' field to each object child that contains a 'name' field */
function addUniqueNames(obj) {
    if (Object.hasOwn(obj, "name")) {
        const name = obj["name"];
        let uname = name;
        let idx = 0;

        while (UNAMES.has(uname)) {
            uname = `${name}${++idx}`;
        }

        UNAMES.add(uname);
        obj["uname"] = uname;
    }

    for (const value of Object.values(obj)) {
        if (typeof value === 'object' && value) {
            addUniqueNames(value)
        } else if (typeof value === 'array') {
            value.forEach((el) => {
                if (typeof el === 'object') {
                    addUniqueNames(el)
                }
            });
        }
    }
}

/**
 * returns an html div that represents a documented registry. errors are
 * handled by creating 
 */
export default async function gautodoc() {
    const reg = await fetchRegistry();
    if (!reg) return errorDiv(`couldn't fetch registry at ${REGISTRY_URL}`);

    addUniqueNames(reg);

    return makeDiv('gautodoc', [
        renderIndex(reg),
        makeDiv('modules', reg.modules.map(renderModule)),
    ]);
}
