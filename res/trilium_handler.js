// see https://github.com/zadam/trilium/wiki/Custom-request-handler

const {req, res} = api;
const {pythonClientToken, objtype, objid, methodName, args} = req.body;

if (pythonClientToken !== api.currentNote.getLabel("pythonClientToken").value) {
    res.send(401);
    return;
}

api.log('Executing '+objtype+'('+objid+').'+methodName+'('+JSON.stringify(args)+')');

// Determine target object
var obj = api;
if ('note' == objtype) {
    obj = api.getNote(objid);
} else if ('branch' == objtype) {
    obj = api.getBranch(objid);
} else if ('attribute' == objtype) {
    obj = api.getAttribute(objid);
} else if ('sql' == objtype) {
    obj = api.sql;
}    

var ret = obj[methodName];
try {
    if ('function' == typeof obj[methodName]) {
        ret = Reflect.apply(obj[methodName], obj, args);
    }
}
catch (e) {
    api.log(e);
    res.status(500).send(String(e));
    return;
}

function replacer(key, value) {
  // Filtering out properties
  if (key === 'children' || key === 'parents') {
    return undefined;
  }
  return value;
}

api.log('Return value ' + JSON.stringify(ret, replacer));
if (ret !== null) {
    res.status(201).send(JSON.stringify(ret, replacer));
}
else {
    res.send(400);
}
