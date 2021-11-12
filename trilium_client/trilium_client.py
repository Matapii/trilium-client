from enum import Enum
import json

import requests


class NoteType(Enum):
    TEXT = 'text'
    CODE = 'code'
    FILE = 'file'
    IMAGE = 'image'
    SEARCH = 'search'
    BOOK = 'book'
    RELATION_MAP = 'relation-map'


def CreateNewNoteParams(parentNoteId, title, content, type,
                        mime=None, isProtected=False, isExpanded=False, prefix='', notePosition=None):
    """CreateNewNoteParams

    @property {string} parentNoteId - MANDATORY
    @property {string} title - MANDATORY
    @property {string|buffer} content - MANDATORY
    @property {string} type - text, code, file, image, search, book, relation-map - MANDATORY
    @property {string} mime - value is derived from default mimes for type
    @property {boolean} isProtected - default is false
    @property {boolean} isExpanded - default is false
    @property {string} prefix - default is empty string
    @property {int} notePosition - default is last existing notePosition in a parent + 10
    """
    params = dict(parentNoteId=parentNoteId,
                  title=title,
                  content=content,
                  type=type.value,
                  isProtected=isProtected,
                  isExpanded=isExpanded,
                  prefix=prefix,
                  )
    if mime is not None:
        params['mime'] = mime
    if notePosition is not None:
        params['notePosition'] = notePosition
    return params


def CreateNoteAttribute():
    """CreateNoteAttribute

    @property {string} type - attribute type - label, relation etc.
    @property {string} name - attribute name
    @property {string} [value] - attribute value
    """
    raise Exception("Not implemented")


def CreateNoteExtraOptions():
    """CreateNoteExtraOptions

    @property {boolean} [json=false] - should the note be JSON
    @property {boolean} [isProtected=false] - should the note be protected
    @property {string} [type='text'] - note type
    @property {string} [mime='text/html'] - MIME type of the note
    @property {CreateNoteAttribute[]} [attributes=[]] - attributes to be created for this note
    """
    raise Exception("Not implemented")


class Client:
    """This is the main backend API interface for scripts."""

    def __init__(self, url, pythonClientToken):
        self.url = url
        self.pythonClientToken = pythonClientToken
        self._session = requests.Session()
        self._sql = Sql(self)

    def _post(self, objtype, objid, method, *args):
        payload = {
            'pythonClientToken': self.pythonClientToken,
            'objtype': objtype,
            'objid': objid,
            'methodName': method,
            'args': args,
        }
        headers = {'content-type': 'application/json'}
        return self._session.post(self.url, data=json.dumps(payload), headers=headers)

    def _request(self, objtype, objid, method, *args):
        r = self._post(objtype, objid, method, *args)
        if r.status_code == 500:
            raise Exception(r.text)
        r.raise_for_status()
        return r.json() if r.text else None

    def _client_request(self, method, *args):
        return self._request('api', None, method, *args)

    @property
    def sql(self):
        return self._sql

    @property
    def startNote(self):
        """{Note} note where script started executing"""
        return Note(self._client_request('startNote'), self)

    @property
    def currentNote(self):
        """{Note} note where script is currently executing. Don't mix this up with concept of active note."""
        return Note(self._client_request('currentNote'), self)

    @property
    def originEntity(self):
        """{Entity} entity whose event triggered this executions"""
        return self._client_request('originEntity')

    def getInstanceName(self):
        """Instance name identifies particular Trilium instance. 

        It can be useful for scripts if some action needs to happen on only one specific instance.
        @returns {string|null}
        """
        return self._client_request('getInstanceName')

    def getNote(self, noteId):
        """Get note by ID.

        @param {string} noteId
        @returns {Note|null}
        """
        data = self._client_request('getNote', noteId)
        return Note(data, self) if data is not None else None

    def getBranch(self, branchId):
        """Get branch by id.

        @param {string} branchId
        @returns {Branch|null}
        """
        branch = self._client_request('getBranch', branchId)
        return Branch(branch, self) if branch is not None else None

    def getAttribute(self, attributeId):
        """Get attribute by id.

        @param {string} attributeId
        @returns {Attribute|null}
        """
        data = self._client_request('getAttribute', attributeId)
        return Attribute(data, self) if data is not None else None

    # def getEntity(self, SQL, array):
        # """Retrieves first entity from the SQL's result set.
        #
        # @param {string} SQL query
        # @param {Array.<?>} array of params
        # @returns {Entity|null}
        # """
        # raise Exception("Not implemented")
        #
    # def getEntities(self, SQL, array):
        # """Retrieves entities from the SQL's result set.
        #
        # @param {string} SQL query
        # @param {Array.<?>} array of params
        # @returns {Entity[]}
        # """
        # raise Exception("Not implemented")

    def searchForNotes(self, query, searchParams=None):
        """This is a powerful search method.

        you can search by attributes and their values, e.g.: "#dateModified =* MONTH AND #log". 
        See full documentation for all options at: https://github.com/zadam/trilium/wiki/Search

        @param {string} query
        @param {Object} [searchParams] Dict with following keys:
            includeArchivedNotes, 
            fastSearch,
            ancestorNoteId, 
            ancestorDepth, 
            includeArchivedNotes, 
            orderBy, 
            orderDirection, 
            limit, 
            debug, 
            fuzzyAttributeSearch, 
        @returns {Note[]}
        """
        args = [query]
        if searchParams is not None:
            args += [searchParams]
        return [Note(data, self) for data in self._client_request('searchForNotes', *args)]

    def searchForNote(self, searchString):
        """This is a powerful search method.

        you can search by attributes and their values, e.g.: "#dateModified =* MONTH AND #log". 
        See full documentation for all options at: https://github.com/zadam/trilium/wiki/Search
        @param {string} searchString
        @returns {Note|null}
        """
        data = self._client_request('searchForNote', searchString)
        return Note(data, self) if data is not None else None

    def getNotesWithLabel(self, name, value=None):
        """Retrieves notes with given label name & value.

        @param {string} name - attribute name
        @param {string} [value] - attribute value
        @returns {Note[]}
        """
        args = [name]
        if value is not None:
            args += [value]
        return [Note(data, self) for data in self._client_request('getNotesWithLabel', *args)]

    def getNoteWithLabel(self, name, value=None):
        """Retrieves first note with given label name & value

        @param {string} name - attribute name
        @param {string} [value] - attribute value
        @returns {Note|null}
        """
        args = [name]
        if value is not None:
            args += [value]
        data = self._client_request('getNoteWithLabel', *args)
        return Note(data, self) if data is not None else None

    def ensureNoteIsPresentInParent(self, noteId, parentNoteId, prefix=None):
        """If there's no branch between note and parent note, create one. Otherwise do nothing.

        @param {string} noteId
        @param {string} parentNoteId
        @param {string} prefix - if branch will be create between note and parent note, set this prefix
        @returns {void}
        """
        return self._client_request('ensureNoteIsPresentInParent', noteId, parentNoteId, prefix)

    def ensureNoteIsAbsentFromParent(self, noteId, parentNoteId):
        """If there's a branch between note and parent note, remove it. Otherwise do nothing.

        @param {string} noteId
        @param {string} parentNoteId
        @returns {void}
        """
        return self._client_request('ensureNoteIsAbsentFromParent', noteId, parentNoteId)

    def toggleNoteInParent(self, present, noteId, parentNoteId, prefix=None):
        """Based on the value, either create or remove branch between note and parent note.

        @param {boolean} present - true if we want the branch to exist, false if we want it gone
        @param {string} noteId
        @param {string} parentNoteId
        @param {string} prefix - if branch will be create between note and parent note, set this prefix
        @returns {void}
        """
        return self._client_request('toggleNoteInParent', present, noteId, parentNoteId, prefix)

    def createTextNote(self, parentNoteId, title, content):
        """Create text note. See also createNewNote() for more options.

        @param {string} parentNoteId
        @param {string} title
        @param {string} content
        @return {{note: Note, branch: Branch}}
        """
        data = self._client_request('createTextNote', parentNoteId, title, content)
        return Note(data['note'], self), Branch(data['branch'], self)

    def createDataNote(self, parentNoteId, title, content):
        """Create data note - data in this context means object serializable to JSON. 

        Created note will be of type 'code' and JSON MIME type. See also createNewNote() for more options.

        @param {string} parentNoteId
        @param {string} title
        @param {object} content
        @return {{note: Note, branch: Branch}}
        """
        data = self._client_request('createDataNote', parentNoteId, title, content)
        return Note(data['note'], self), Branch(data['branch'], self)

    def createNewNote(self, params):
        """createNewNote

        @param {CreateNewNoteParams} [params]
        @returns {{note: Note, branch: Branch}} object contains newly created entities note and branch
        """
        data = self._client_request('createNewNote', params)
        return Note(data['note'], self), Branch(data['branch'], self)

    def log(self, message):
        """Log given message to trilium logs.

        @param message
        """
        return self._client_request('log', message)

    def getRootCalendarNote(self):
        """Returns root note of the calendar.

        @returns {Note|null}
        """
        data = self._client_request('getRootCalendarNote')
        return Note(data, self) if data is not None else None

    def getDateNote(self, date):
        """Returns day note for given date. If such note doesn't exist, it is created.

         @param {string} date in YYYY-MM-DD format
         @returns {Note|null}
         """
        data = self._client_request('getDateNote', date)
        return Note(data, self) if data is not None else None

    def getTodayNote(self):
        """Returns today's day note. If such note doesn't exist, it is created.

        @returns {Note|null}
        """
        data = self._client_request('getTodayNote')
        return Note(data, self) if data is not None else None

    def getWeekNote(self, date, options):
        """Returns note for the first date of the week of the given date.

        @param {string} date in YYYY-MM-DD format
        @param {object} options - "startOfTheWeek" - either "monday" (default) or "sunday"
        @returns {Note|null}
        """
        data = self._client_request('getWeekNote', date, options)
        return Note(data, self) if data is not None else None

    def getMonthNote(self, date):
        """Returns month note for given date. If such note doesn't exist, it is created.

        @param {string} date in YYYY-MM format
        @returns {Note|null}
        """
        data = self._client_request('getMonthNote', date)
        return Note(data, self) if data is not None else None

    def getYearNote(self, year):
        """Returns year note for given year. If such note doesn't exist, it is created.

        @param {string} year in YYYY format
        @returns {Note|null}
        """
        data = self._client_request('getYearNote', year)
        return Note(data, self) if data is not None else None

    def sortNotesAlphabetically(self, parentNoteId):
        """sortNotesAlphabetically

        @param {string} parentNoteId - this note's child notes will be sorted
        """
        return self._client_request('sortNotesAlphabetically', parentNoteId)

    # def setNoteToParent(self, noteId, prefix, parentNoteId):
        # """This method finds note by its noteId and prefix and either sets it to the given parentNoteId
        # or removes the branch (if parentNoteId is not given).
        #
        # This method looks similar to toggleNoteInParent() but differs because we're looking up branch by prefix.
        #
        # @param {string} noteId
        # @param {string} prefix
        # @param {string|null} parentNoteId
        # """
        # return self._client_request('setNoteToParent', noteId, prefix, parentNoteId)

    # def transactional(self, noteId, prefix, parentNoteId):
        # """This functions wraps code which is supposed to be running in transaction.
        #
        # If transaction already exists, then we'll use that transaction.
        # @param {function} func
        # @returns {?} result of func callback
        # """
        # raise Exception("Not implemented")

    def getAppInfo(self):
        """getAppInfo

        @return {{syncVersion, appVersion, buildRevision, dbVersion, dataDirectory, buildDate}|*} 
         - object representing basic info about running Trilium version
        """
        return self._client_request('getAppInfo')


class Note:
    """This represents a Note which is a central object in the Trilium Notes project."""

    def __init__(self, data, client):
        self._data = data
        self._client = client

    def __repr__(self):
        return "Note '" + self.title + "' " + repr(self._data)

    def _client_request(self, method, *args):
        return self._client._request('note', self.noteId, method, *args)

    @property
    def noteId(self):
        """{string} noteId - primary key"""
        return self._data['noteId']

    @property
    def type(self):
        """{string} type - one of "text", "code", "file" or "render" """
        return self._data['type']

    @property
    def mime(self):
        """{string} mime - MIME type, e.g. "text/html" """
        return self._data['mime']

    @property
    def title(self):
        """{string} title - note title"""
        return self._data['title']

    @property
    def isProtected(self):
        """{boolean} isProtected - true if note is protected"""
        return self._data['isProtected']

    @property
    def isDeleted(self):
        """{boolean} isDeleted - true if note is deleted"""
        return self._data['isDeleted']

    @property
    def deleteId(self):
        """{string|null} deleteId - ID identifying delete transaction"""
        return self._data['deleteId']

    @property
    def dateCreated(self):
        """{string} dateCreated - local date time (with offset)"""
        return self._data['dateCreated']

    @property
    def dateModified(self):
        """{string} dateModified - local date time (with offset)"""
        return self._data['dateModified']

    @property
    def utcDateCreated(self):
        """{string} utcDateCreated"""
        return self._data['utcDateCreated']

    @property
    def utcDateModified(self):
        """{string} utcDateModified"""

    def getContent(self):
        """Loads the content"""
        return self._client_request('getContent')

    def getContentMetadata(self):
        """@returns {{contentLength, dateModified, utcDateModified}} """
        return self._client_request('getContentMetadata')

    def getJsonContent(self):
        """@returns {*}"""
        return self._client_request('getJsonContent')

    def setContent(self, content):
        return self._client_request('setContent', content)

    def setJsonContent(self, content):
        return self._client_request('setJsonContent', content)

    def isRoot(self):
        """{boolean} true if this note is the root of the note tree. Root note has "root" noteId"""
        return self._client_request('isRoot')

    def isJson(self):
        """{boolean} true if this note is of application/json content type """
        return self._client_request('isJson')

    def isJavaScript(self):
        """@returns {boolean} true if this note is JavaScript (code or attachment)"""
        return self._client_request('isJavaScript')

    def isHtml(self):
        """@returns {boolean} true if this note is HTML"""
        return self._client_request('isHtml')

    def isStringNote(self):
        """@returns {boolean} true if the note has string content (not binary)"""
        return self._client_request('isStringNote')

    def getScriptEnv(self):
        """@returns {string} JS script environment - either "frontend" or "backend"""
        return self._client_request('getScriptEnv')

    def getOwnedAttributes(self, type=None, name=None):
        """This method is a faster variant of getAttributes() which looks for only owned attributes.

        Use when inheritance is not needed and/or in batch/performance sensitive operations.
        @param {string} [type] - (optional) attribute type to filter
        @param {string} [name] - (optional) attribute name to filter
        @returns {Attribute[]} note's "owned" attributes - excluding inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getOwnedAttributes', type, name)]

    def getOwnedAttribute(self, type, name):
        """@returns {Attribute} attribute belonging to this specific note (excludes inherited attributes)

        This method can be significantly faster than the getAttribute()
        """
        data = self._client_request('getOwnedAttribute', type, name)
        return Attribute(data, self._client) if data is not None else None

    def getTargetRelations(self):
        """@returns {Attribute[]} relations targetting this specific note"""
        return [Attribute(data, self._client) for data in self._client_request('getTargetRelations')]

    def getAttributes(self, type=None, name=None):
        """   getAttributes  * 

        @param {string} [type] - (optional) attribute type to filter
        @param {string} [name] - (optional) attribute name to filter
        @returns {Attribute[]} all note's attributes, including inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getAttributes', type, name)]

    def getLabels(self, name=None):
        """getLabels

        @param {string} [name] - label name to filter
        @returns {Attribute[]} all note's labels (attributes with type label), including inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getLabels', name)]

    def getOwnedLabels(self, name=None):
        """getOwnedLabels

        @param {string} [name] - label name to filter
        @returns {Attribute[]} all note's labels (attributes with type label), excluding inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getOwnedLabels', name)]

    def getRelations(self, name=None):
        """getRelations

        @param {string} [name] - relation name to filter
        @returns {Attribute[]} all note's relations (attributes with type relation), including inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getRelations', name)]

    def getOwnedRelations(self, name=None):
        """getOwnedRelations

        @param {string} [name] - relation name to filter
        @returns {Attribute[]} all note's relations (attributes with type relation), excluding inherited ones
        """
        return [Attribute(data, self._client) for data in self._client_request('getOwnedRelations', name)]

    def getRelationTargets(self, name=None):
        """getRelationTargets

        @param {string} [name] - relation name to filter
        @returns {Note[]}
        """
        return [self._client.getNote(relation.value) for relation in self.getRelations()]

    def hasAttribute(self, type, name):
        """hasAttribute

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @returns {boolean} true if note has an attribute with given type and name (including inherited)
        """
        return self._client_request('hasAttribute', type, name)

    def hasOwnedAttribute(self, type, name):
        """hasOwnedAttribute

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @returns {boolean} true if note has an attribute with given type and name (excluding inherited)
        """
        return self._client_request('hasOwnedAttribute', type, name)

    def getAttribute(self, type, name):
        """getAttribute

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @returns {Attribute} attribute of given type and name. If there's more such attributes, first is  returned. 
        Returns null if there's no such attribute belonging to this note.
        """
        data = self._client_request('getAttribute', type, name)
        return Attribute(data, self._client) if data is not None else None

    def getAttributeValue(self, type, name):
        """getAttributeValue

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @returns {string|null} attribute value of given type and name or null if no such attribute exists.
        """
        return self._client_request('getAttributeValue', type, name)

    def getOwnedAttributeValue(self, type, name):
        """getOwnedAttributeValue

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @returns {string|null} attribute value of given type and name or null if no such attribute exists.
        """
        return self._client_request('getOwnedAttributeValue', type, name)

    def toggleAttribute(self, type, enabled, name, value=None):
        """Based on enabled, attribute is either set or removed.

        @param {string} type - attribute type ('relation', 'label' etc.)
        @param {boolean} enabled - toggle On or Off
        @param {string} name - attribute name
        @param {string} [value] - attribute value (optional)
        """
        return self._client_request('toggleAttribute', type, enabled, name, value)

    def setAttribute(self, type, name, value=None):
        """Update's given attribute's value or creates it if it doesn't exist

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @param {string} [value] - attribute value (optional)
        """
        return self._client_request('setAttribute', type, name, value)

    def removeAttribute(self, type, name, value=None):
        """Removes given attribute name-value pair if it exists.

        @param {string} type - attribute type (label, relation, etc.)
        @param {string} name - attribute name
        @param {string} [value] - attribute value (optional)
        """
        return self._client_request('removeAttribute', type, name, value)

    def addAttribute(self, type, name, value="", isInheritable=False, position=1000):
        """@return {Attribute}"""
        data = self._client_request('addAttribute', type, name, value, isInheritable, position)
        return Attribute(data, self._client) if data is not None else None

    def addLabel(self, name, value="", isInheritable=False):
        data = self._client_request('addLabel', name, value, isInheritable)
        return Attribute(data, self._client) if data is not None else None

    def addRelation(self, name, targetNoteId, isInheritable=False):
        data = self._client_request('addRelation', name, targetNoteId, isInheritable)
        return Attribute(data, self._client) if data is not None else None

    def hasLabel(self, name):
        """hasLabel

        @param {string} name - label name
        @returns {boolean} true if label exists (including inherited)
        """
        return self._client_request('hasLabel', name)

    def hasOwnedLabel(self, name):
        """hasOwnedLabel

        @param {string} name - label name
        @returns {boolean} true if label exists (excluding inherited)
        """
        return self._client_request('hasOwnedLabel', name)

    def hasRelation(self, name):
        """hasRelation

        @param {string} name - relation name
        @returns {boolean} true if relation exists (including inherited)
        """
        return self._client_request('hasRelation', name)

    def hasOwnedRelation(self, name):
        """hasOwnedRelation

        @param {string} name - relation name
        @returns {boolean} true if relation exists (excluding inherited)
        """
        return self._client_request('hasOwnedRelation', name)

    def getLabel(self, name):
        """getLabel
        @param {string} name - label name
        @returns {Attribute|null} label if it exists, null otherwise
        """
        data = self._client_request('getLabel', name)
        return Attribute(data, self._client) if data is not None else None

    def getOwnedLabel(self, name):
        """getOwnedLabel

        @param {string} name - label name
        @returns {Attribute|null} label if it exists, null otherwise
        """
        data = self._client_request('getOwnedLabel', name)
        return Attribute(data, self._client) if data is not None else None

    def getRelation(self, name):
        """getRelation

        @param {string} name - relation name
        @returns {Attribute|null} relation if it exists, null otherwise
        """
        data = self._client_request('getRelation', name)
        return Attribute(data, self._client) if data is not None else None

    def getOwnedRelation(self, name):
        """getOwnedRelation

        @param {string} name - relation name
        @returns {Attribute|null} relation if it exists, null otherwise
        """
        data = self._client_request('getOwnedRelation', name)
        return Attribute(data, self._client) if data is not None else None

    def getLabelValue(self, name):
        """getLabelValue

        @param {string} name - label name
        @returns {string|null} label value if label exists, null otherwise
        """
        return self._client_request('getLabelValue', name)

    def getOwnedLabelValue(self, name):
        """getOwnedLabelValue

        @param {string} name - label name
        @returns {string|null} label value if label exists, null otherwise
        """
        return self._client_request('getOwnedLabelValue', name)

    def getRelationValue(self, name):
        """getRelationValue

        @param {string} name - relation name
        @returns {string|null} relation value if relation exists, null otherwise
        """
        return self._client_request('getRelationValue', name)

    def getOwnedRelationValue(self, name):
        """getOwnedRelationValue

        @param {string} name - relation name
        @returns {string|null} relation value if relation exists, null otherwise
        """
        return self._client_request('getOwnedRelationValue', name)

    def getRelationTarget(self, name):
        """getRelationTarget

        @param {string} name
        @returns {Note|null} target note of the relation or null (if target is empty or note was not found)
        """
        data = self._client_request('getRelationTarget', name)
        return Note(data, self._client) if data is not None else None

    def getOwnedRelationTarget(self, name):
        """getOwnedRelationTarget

        @param {string} name
        @returns {Note|null} target note of the relation or null (if target is empty or note was not found)
        """
        data = self._client_request('getOwnedRelationTarget', name)
        return Note(data, self._client) if data is not None else None

    def toggleLabel(self, enabled, name, value=None):
        """Based on enabled, label is either set or removed.

        @param {boolean} enabled - toggle On or Off
        @param {string} name - label name
        @param {string} [value] - label value (optional)
        """
        return self._client_request('toggleLabel', enabled, name, value)

    def toggleRelation(self, enabled, name, value=None):
        """Based on enabled, relation is either set or removed.

        @param {boolean} enabled - toggle On or Off
        @param {string} name - relation name
        @param {string} [value] - relation value (noteId)
        """
        return self._client_request('toggleRelation', enabled, name, value)

    def setLabel(self, name, value=None):
        """Update's given label's value or creates it if it doesn't exist

        @param {string} name - label name
        @param {string} [value] - label value
        """
        return self._client_request('setLabel', name, value)

    def setRelation(self, name, value=None):
        """Update's given relation's value or creates it if it doesn't exist

        @param {string} name - relation name
        @param {string} [value] - relation value (noteId)
        """
        return self._client_request('setRelation', name, value)

    def removeLabel(self, name, value=None):
        """Remove label name-value pair, if it exists.

        @param {string} name - label name
        @param {string} [value] - label value
        """
        return self._client_request('removeLabel', name, value)

    def removeRelation(self, name, value=None):
        """Remove relation name-value pair, if it exists.

        @param {string} name - relation name
        @param {string} [value] - relation value (noteId)
        """
        return self._client_request('removeRelation', name, value)

    def getDescendantNoteIds(self):
        """@return {string[]} return list of all descendant noteIds of this note. Returning just noteIds because number of notes can be huge. Includes also this note's noteId"""
        return self._client_request('getDescendantNoteIds')

    # def getDescendantNotesWithAttribute(self, type, name, value=None):
    #     """Finds descendant notes with given attribute name and value. Only own attributes are considered, not inherited ones
    #
    #     @param {string} type - attribute type (label, relation, etc.)
    #     @param {string} name - attribute name
    #     @param {string} [value] - attribute value
    #     @returns {Note[]}
    #     """
    #     args = [type, name]
    #     if value is not None:
    #         args += [value]
    #     return [Note(data, self._client) for data in self._client_request('getDescendantNotesWithAttribute', *args)]

    # def getDescendantNotesWithLabel(self, name, value=None):
    #     """Finds descendant notes with given label name and value. Only own labels are considered, not inherited ones
    #
    #     @param {string} name - label name
    #     @param {string} [value] - label value
    #     @returns {Note[]}
    #     """
    #     args = [name]
    #     if value is not None:
    #         args += [value]
    #     return [Note(data, self._client) for data in self._client_request('getDescendantNotesWithLabel', *args)]
    #
    # def getDescendantNotesWithRelation(self, name, value=None):
    #     """Finds descendant notes with given relation name and value. Only own relations are considered, not inherited ones
    #
    #     @param {string} name - relation name
    #     @param {string} [value] - relation value
    #     @returns {Note[]}
    #     """
    #     args = [name]
    #     if value is not None:
    #         args += [value]
    #     return [Note(data, self._client) for data in self._client_request('getDescendantNotesWithRelation', *args)]

    def getNoteRevisions(self):
        """Returns note revisions of this note.

        @returns {NoteRevision[]}
        """
        return [NoteRevision(data, self._client) for data in self._client_request('getNoteRevisions')]

    def getBranches(self):
        branches = self._client_request('getBranches')
        return [Branch(branch, self._client) for branch in branches]

    def hasChildren(self):
        """ {boolean} - true if note has children"""
        return self._client_request('hasChildren')

    def getChildNotes(self):
        """getChildNotes

        @returns {Note[]} child notes of this note
        """
        return [Note(data, self._client) for data in self._client_request('getChildNotes')]

    def getChildBranches(self):
        """getChildBranches

        @returns {Branch[]} child branches of this note
        """
        return [Branch(data, self._client) for data in self._client_request('getChildBranches')]

    def getParentNotes(self):
        """getParentNotes

        @returns {Note[]} parent notes of this note (note can have multiple parents because of cloning)
        """
        return [Note(data, self._client) for data in self._client_request('getParentNotes')]

    def getAllNotePaths(self):
        """getAllNotePaths
        @return {string[][]} - array of notePaths (each represented by array of noteIds constituting the particular note path)
        """
        return self._client_request('getAllNotePaths')

    def isDescendantOfNote(self, ancestorNoteId):
        """isDescendantOfNote

        @param ancestorNoteId
        @return {boolean} - true if ancestorNoteId occurs in at least one of the note's paths
        """
        return self._client_request('isDescendantOfNote', ancestorNoteId)


class Branch:
    """Branch represents note's placement in the tree - it's essentially pair of noteId and parentNoteId.

    Each note can have multiple (at least one) branches, meaning it can be placed into multiple places in the tree.
    """

    def __init__(self, data, client):
        self._data = data
        self._client = client

    def __repr__(self):
        return "Branch " + repr(self._data)

    def _client_request(self, method, *args):
        return self._client._request('branch', self.branchId, method, *args)

    @property
    def branchId(self):
        """{string} branchId - primary key, immutable"""
        return self._data['branchId']

    @property
    def noteId(self):
        """{string} noteId - immutable"""
        return self._data['noteId']

    @property
    def parentNoteId(self):
        """{string} parentNoteId - immutable"""
        return self._data['parentNoteId']

    @property
    def notePosition(self):
        """{int} notePosition"""
        return self._data['notePosition']

    @property
    def prefix(self):
        """{string} prefix"""
        return self._data['prefix']

    @property
    def isExpanded(self):
        """{boolean} isExpanded"""
        return self._data['isExpanded']

    @property
    def isDeleted(self):
        """{boolean} isDeleted"""
        return self._data['isDeleted']

    @property
    def deleteId(self):
        """{string|null} deleteId - ID identifying delete transaction"""
        return self._data['deleteId']

    @property
    def utcDateModified(self):
        """{string} utcDateModified"""
        return self._data['utcDateModified']

    @property
    def utcDateCreated(self):
        """{string} utcDateCreated"""
        return self._data['utcDateCreated']

    def getNote(self):
        """@returns {Note|null}"""
        return self._client.getNote(self.noteId)

    def getParentNote(self):
        """@returns {Note|null}"""
        return self._client.getNote(self.parentNoteId)


class Attribute:
    """Attribute is key value pair owned by a note."""

    def __init__(self, data, client):
        self._data = data
        self._client = client

    def __repr__(self):
        return "Attribute '" + self.name + "' " + repr(self._data)

    def _client_request(self, method, *args):
        return self._client._request('attribute', self.attributeId, method, *args)

    @property
    def attributeId(self):
        """@property {string} attributeId - immutable"""
        return self._data['attributeId']

    @property
    def noteId(self):
        """{string} noteId - immutable"""
        return self._data['noteId']

    @property
    def type(self):
        """{string} type - immutable"""
        return self._data['type']

    @property
    def name(self):
        """{string} name - immutable"""
        return self._data['name']

    @property
    def value(self):
        """{string} value"""
        return self._data['value']

    @property
    def position(self):
        """{int} position"""
        return self._data['position']

    @property
    def isInheritable(self):
        """{boolean} isInheritable - immutable"""
        return self._data['isInheritable']

    @property
    def isDeleted(self):
        """{boolean} isDeleted - true if note is deleted"""
        return self._data['isDeleted']

    @property
    def deleteId(self):
        """{string|null} deleteId - ID identifying delete transaction"""
        return self._data['deleteId']

    @property
    def utcDateModified(self):
        """{string} utcDateModified"""

    def getNote(self):
        """@returns {Note|null}"""
        return Note(self._client_request('getNote'), self._client)

    def getTargetNote(self):
        """@returns {Note|null}"""
        return Note(self._client_request('getTargetNote'), self._client)

    def isDefinition(self):
        """@return {boolean}"""
        return self._client_request('isDefinition')


class NoteRevision:
    """NoteRevision represents snapshot of note's title and content at some point in the past. It's used for seamless note versioning."""

    def __init__(self, data, client):
        self._data = data
        self._client = client

    def __repr__(self):
        return "NoteRevision '" + self.title + "' " + repr(self._data)

    def _client_request(self, method, *args):
        return self._client._request('noterevision', self.attributeId, method, *args)

    @property
    def noteRevisionId(self):
        """{string} noteRevisionId"""
        return self._data['noteRevisionId']

    @property
    def noteId(self):
        """{string} noteId - immutable"""
        return self._data['noteId']

    @property
    def type(self):
        """{string} type - one of "text", "code", "file" or "render" """
        return self._data['type']

    @property
    def mime(self):
        """{string} mime - MIME type, e.g. "text/html" """
        return self._data['mime']

    @property
    def title(self):
        """{string} title - note title"""
        return self._data['title']

    @property
    def isProtected(self):
        """{boolean} isProtected - true if note is protected"""
        return self._data['isProtected']

    @property
    def dateLastEdited(self):
        """{string} dateLastEdited"""
        return self._data['dateLastEdited']

    @property
    def dateCreated(self):
        """{string} dateCreated - local date time (with offset)"""
        return self._data['dateCreated']

    @property
    def utcDateLastEdited(self):
        """{string} utcDateLastEdited"""
        return self._data['utcDateLastEdited']

    @property
    def utcDateCreated(self):
        """{string} utcDateCreated"""
        return self._data['utcDateCreated']

    @property
    def utcDateModified(self):
        """{string} utcDateModified"""

    # TBD getNote()
    # TBD isStringNote()
    # TBD getContent()


class Option:
    """Option represents name-value pair, either directly configurable by the user or some system property."""


class Sql:
    """Direct access to the SQL database."""

    def __init__(self, client):
        self._client = client

    def __repr__(self):
        return "Sql"

    def _client_request(self, method, *args):
        return self._client._request('sql', 'sql', method, *args)

    def execute(self, query, params=[]):
        return self._client_request('execute', query, params)

    def getRows(self, query, params=[]):
        return self._client_request('getRows', query, params)
