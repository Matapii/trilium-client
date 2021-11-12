# pytest --cov=trilium_client
# coverage html

import json
import os
import pytest

from requests.exceptions import ConnectionError
import requests

from trilium_client import *


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("trilium", 8080)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url


@pytest.fixture
def client(http_service):
    TRILIUM_URL = http_service + '/custom/python-client'
    TRILIUM_CLIENT_TOKEN = '123'
    client = Client(TRILIUM_URL, TRILIUM_CLIENT_TOKEN)
    return client


@pytest.fixture(scope="function")
def text_note(client):
    parent = client.getNote('root')
    new_note = client.createTextNote(parent.noteId, 'new note', 'test')[0]
    yield new_note
    client.ensureNoteIsAbsentFromParent(new_note.noteId, parent.noteId)


@pytest.fixture(scope="function")
def json_note(client):
    parent = client.getNote('root')
    new_note = client.createNewNote(CreateNewNoteParams('root', 'test3', '0', NoteType.CODE,
                                                        mime='application/json'))[0]
    yield new_note
    client.ensureNoteIsAbsentFromParent(new_note.noteId, parent.noteId)


@pytest.fixture(scope="function")
def code_note(client):
    parent = client.getNote('root')
    new_note = client.createDataNote(parent.noteId, 'new note', 'test')[0]
    yield new_note
    client.ensureNoteIsAbsentFromParent(new_note.noteId, parent.noteId)


def test_get_appinfo(client):
    appInfo = client.getAppInfo()
    assert appInfo['appVersion']


def test_current_note(client):
    currentNote = client.currentNote
    assert currentNote.noteId

    repr(currentNote)
    currentNote.type
    currentNote.mime
    currentNote.dateCreated
    currentNote.dateModified
    currentNote.utcDateCreated


def test_start_note(client):
    startNote = client.startNote
    assert startNote.noteId


def test_origin_note(client):
    client.originEntity


def test_instance_name(client):
    client.getInstanceName()


def test_get_note(client, text_note):
    assert client.getNote('root').noteId == 'root'
    assert client.getNote(text_note.noteId).noteId == text_note.noteId


def test_get_content(client, text_note):
    node = client.getNote(text_note.noteId)
    node.setContent('test')
    assert node.getContent() == 'test'
    assert node.getContentMetadata()['contentLength'] > 0


def test_get_branches(client, text_note):
    note = client.getNote('root')
    assert len(note.getBranches()) == 0
    assert note.hasChildren()

    note = text_note
    assert len(note.getBranches()) >= 0
    assert not note.hasChildren()

    branch = note.getBranches()[0]
    assert branch.branchId

    assert client.getBranch(branch.branchId).branchId == branch.branchId

    assert branch.getNote().noteId

    assert branch.getNote().noteId == branch.noteId
    assert branch.getParentNote().noteId == branch.parentNoteId
    assert branch.getParentNote().noteId


def test_json_content(client, json_note):
    note = json_note
    assert 0 == note.getJsonContent()

    note.setContent('4')
    assert 4 == note.getJsonContent()

    note.setJsonContent(9)
    assert 9 == note.getJsonContent()

    assert note.isJson()
    assert False == client.getNote('root').isJson()
    assert not note.isJavaScript()
    assert not note.isHtml()
    assert note.isStringNote()


def test_is_root(client):
    assert client.getNote('root').isRoot()
    assert not client.getNote('root').getChildNotes()[0].isRoot()


def test_get_script_env(client):
    currentNote = client.currentNote
    assert 'backend' == currentNote.getScriptEnv()


def test_attribute_label(client, text_note):

    # create label
    note = text_note
    note.setAttribute('label', 'test_label', 'bar3')

    # check count
    assert len(note.getOwnedAttributes(None, None)) > 0
    assert len(note.getOwnedAttributes('label', None)) > 0
    assert len(note.getOwnedAttributes(None, 'test_label')) == 1
    assert len(note.getOwnedAttributes('label', 'test_label')) == 1

    assert len(note.getAttributes()) > 0

    assert len(note.getLabels()) > 0

    assert len(note.getOwnedLabels()) > 0

    # test label
    attr = note.getOwnedAttributes('label', 'test_label')[0]
    assert attr.getNote().noteId == note.noteId
    assert not attr.isDefinition()

    assert note.getOwnedAttribute('label', 'test_label').attributeId == attr.attributeId

    assert client.getAttribute(attr.attributeId).attributeId == attr.attributeId

    assert note.getAttribute('label', 'test_label').attributeId == attr.attributeId

    # assert note.getOwnedAttribute(None, 'customRequestHandler').attributeId

    # Test toggle
    note.toggleAttribute('label', False, 'test_label', 'bar3')
    assert not note.hasLabel('test_label')
    assert not note.hasOwnedLabel('test_label')

    note.toggleAttribute('label', True, 'test_label', 'bar2')
    assert note.hasLabel('test_label')
    assert note.hasOwnedLabel('test_label')

    # Test set
    note.setAttribute('label', 'test_label', 'bar4')
    assert note.getLabel('test_label')
    assert note.getOwnedLabel('test_label')
    assert 'bar4' == note.getLabelValue('test_label')
    assert 'bar4' == note.getOwnedLabelValue('test_label')

    # test remove
    note.removeAttribute('label', 'test_label', 'bar4')
    assert not note.hasLabel('test_label')
    assert not note.hasOwnedLabel('test_label')

    # Test add
    note.addAttribute('label', 'test_label', 'bar4', isInheritable=True)
    assert note.hasLabel('test_label')
    assert note.hasOwnedLabel('test_label')

    # test remove
    note.removeAttribute('label', 'test_label', 'bar4')
    assert not note.hasLabel('test_label')
    assert not note.hasOwnedLabel('test_label')

    # Test add
    note.addLabel('test_label', 'bar4')
    assert note.hasLabel('test_label')
    assert note.hasOwnedLabel('test_label')

    # Test toggle
    note.toggleLabel(False, 'test_label', 'bar4')
    assert not note.hasLabel('test_label')
    assert not note.hasOwnedLabel('test_label')

    note.toggleLabel(True, 'test_label', 'bar4')
    assert note.hasLabel('test_label')
    assert note.hasOwnedLabel('test_label')

    # Test set
    assert len(client.getNotesWithLabel('test_label')) == 1
    note.setLabel('test_label', 'bar5')
    assert 'bar5' == note.getLabelValue('test_label')
    assert 'bar5' == note.getOwnedLabelValue('test_label')

    # Test remove
    note.removeLabel('test_label', 'bar5')
    assert not note.hasLabel('test_label')
    assert not note.hasOwnedLabel('test_label')

    # jTest getNotesWithLabel
    note.setAttribute('label', 'test_label', 'bar5')
    assert len(client.getNotesWithLabel('test_label', 'bar5')) == 1
    assert len(client.getNotesWithLabel('test_label')) == 1
    assert client.getNoteWithLabel('test_label')
    assert client.getNoteWithLabel('test_label', 'bar5')


def test_attribute_relation(client, text_note):

    note = text_note
    # test has
    assert not note.hasAttribute('relation', 'test_relation')
    assert not note.hasOwnedAttribute('relation', 'test_relation')
    assert not note.hasRelation('test_relation')
    assert not note.hasOwnedRelation('test_relation')

    # create relation
    note.setAttribute('relation', 'test_relation', 'root')

    # check count
    assert len(note.getOwnedAttributes(None, None)) > 0
    assert len(note.getOwnedAttributes('relation', None)) > 0
    assert len(note.getOwnedAttributes(None, 'test_relation')) == 1
    assert len(note.getOwnedAttributes('relation', 'test_relation')) == 1

    assert len(note.getRelations()) == 1
    assert len(note.getOwnedRelations()) == 1
    assert len(note.getRelationTargets()) == 1

    # test has
    assert note.hasAttribute('relation', 'test_relation')
    assert note.hasOwnedAttribute('relation', 'test_relation')
    assert note.hasRelation('test_relation')
    assert note.hasOwnedRelation('test_relation')

    # test relation
    attr = note.getOwnedAttributes('relation', 'test_relation')[0]
    assert attr.noteId == note.noteId
    assert attr.getTargetNote().noteId == 'root'

    assert len(client.getNote('root').getTargetRelations()) == 1
    assert client.getNote('root').getTargetRelations()[0].attributeId == attr.attributeId

    assert attr.attributeId == note.getAttribute('relation', 'test_relation').attributeId
    assert attr.attributeId == note.getRelation('test_relation').attributeId
    assert attr.attributeId == note.getOwnedRelation('test_relation').attributeId

    assert 'root' == note.getAttributeValue('relation', 'test_relation')
    assert 'root' == note.getOwnedAttributeValue('relation', 'test_relation')
    assert 'root' == note.getRelationValue('test_relation')
    assert 'root' == note.getOwnedRelationValue('test_relation')

    assert 'root' == note.getRelationTarget('test_relation').noteId
    # TODO
    # assert 'root' == note.getOwnedRelationTarget('test_relation').noteId

    note.removeRelation('test_relation', 'root')
    assert not note.hasAttribute('relation', 'test_relation')

    note.toggleRelation(True, 'test_relation', 'root')
    assert note.hasAttribute('relation', 'test_relation')

    note.toggleRelation(False, 'test_relation', 'root')
    assert not note.hasAttribute('relation', 'test_relation')

    note.setRelation('test_relation', 'root')
    assert note.hasAttribute('relation', 'test_relation')


def test_descaendant(client):
    root = client.getNote('root')
    currentNote = client.currentNote

    assert len(root.getDescendantNoteIds()) > 0

    assert not root.isDescendantOfNote(currentNote.noteId)

    assert currentNote.isDescendantOfNote(root.noteId)

    # root.getDescendantNotesWithAttribute('label', 'test_label', 'bar5')

    # root.getDescendantNotesWithAttribute('label', 'test_label')

    # root.getDescendantNotesWithLabel('test_label', 'bar5')

    # root.getDescendantNotesWithLabel('test_label')

    # root.getDescendantNotesWithRelation('test_label')

    # root.getDescendantNotesWithRelation('test_label', 'root')


def test_revisions(client):
    currentNote = client.currentNote

    currentNote.getNoteRevisions()


def test_child_parent(client):
    root = client.getNote('root')
    currentNote = client.currentNote

    assert len(root.getChildNotes()) > 0

    assert len(root.getChildBranches()) > 0

    assert len(root.getParentNotes()) == 0

    assert len(currentNote.getParentNotes()) > 0


def test_all_note_paths(client):
    root = client.getNote('root')
    currentNote = client.currentNote

    assert len(root.getAllNotePaths()) > 0
    assert len(currentNote.getAllNotePaths()) > 0


def test_search(client, json_note):

    assert len(client.searchForNotes('test', dict(limit=2, ancestorNoteId='root'))) > 0

    assert client.searchForNote(json_note.title)


def test_ensure(client):
    root = client.getNote('root')
    currentNote = client.currentNote

    client.ensureNoteIsPresentInParent(currentNote.noteId, root.noteId)

    client.ensureNoteIsAbsentFromParent(currentNote.noteId, root.noteId)

    client.toggleNoteInParent(True, currentNote.noteId, root.noteId)


def test_create(client, text_note, json_note, code_note):
    pass


def test_log(client):
    client.log('test123')


def test_calendar(client):

    assert client.getRootCalendarNote()

    assert client.getDateNote('2021-03-20')

    assert client.getTodayNote()

    assert client.getWeekNote('2021-03-20', dict(startOfTheWeek='monday'))

    assert client.getMonthNote('2021-03-20')

    assert client.getYearNote('2021')


def test_sort(client):

    client.sortNotesAlphabetically('root')
