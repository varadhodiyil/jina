from copy import deepcopy

import pytest
import numpy as np
from scipy.sparse import coo_matrix

from jina import Document
from jina.types.arrays import DocumentArray

DOCUMENTS_PER_LEVEL = 1


@pytest.fixture(scope='function')
def document_factory():
    class DocumentFactory(object):
        def create(self, idx, text):
            with Document(id=idx) as d:
                d.tags['id'] = idx
                d.text = text
            return d

    return DocumentFactory()


@pytest.fixture
def docs(document_factory):
    return [
        document_factory.create(1, 'test 1'),
        document_factory.create(2, 'test 1'),
        document_factory.create(3, 'test 3'),
    ]


@pytest.fixture
def docarray(docs):
    return DocumentArray(docs)


@pytest.fixture
def docarray_with_scipy_sparse_embedding(docs):
    embedding = coo_matrix(
        (
            np.array([1, 2, 3, 4, 5, 6]),
            (np.array([0, 0, 0, 0, 0, 0]), np.array([0, 2, 2, 0, 1, 2])),
        ),
        shape=(1, 10),
    )
    for doc in docs:
        doc.embedding = embedding
    return DocumentArray(docs)


def test_length(docarray, docs):
    assert len(docs) == len(docarray) == 3


def test_append(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    assert docarray[-1].id == doc.id


def test_union(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.append(doc)
    union = docarray + additional_docarray
    for idx in range(0, 3):
        assert union[idx].id == docarray[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docarray[idx].id


def test_union_inplace(docarray, document_factory):
    additional_docarray = DocumentArray([])
    for idx in range(4, 10):
        doc = document_factory.create(idx, f'test {idx}')
        additional_docarray.append(doc)
    union = deepcopy(docarray)
    union += additional_docarray
    for idx in range(0, 3):
        assert union[idx].id == docarray[idx].id
    for idx in range(0, 6):
        assert union[idx + 3].id == additional_docarray[idx].id


def test_extend(docarray, document_factory):
    docs = [document_factory.create(4, 'test 4'), document_factory.create(5, 'test 5')]
    docarray.extend(docs)
    assert len(docarray) == 5
    assert docarray[-1].tags['id'] == 5
    assert docarray[-1].text == 'test 5'


def test_clear(docarray):
    docarray.clear()
    assert len(docarray) == 0


def test_delete(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    docarray.append(doc)
    del docarray[-1]
    assert len(docarray) == 3
    assert docarray == docarray


def test_array_get_success(docarray, document_factory):
    doc = document_factory.create(4, 'test 4')
    doc_id = 2
    docarray[doc_id] = doc
    assert docarray[doc_id].text == 'test 4'
    doc_0_id = docarray[0].id
    docarray[doc_0_id] = doc
    assert docarray[doc_0_id].text == 'test 4'


def test_array_get_from_slice_success(docs, document_factory):
    docarray = DocumentArray(docs)
    assert len(docarray[:1]) == 1
    assert len(docarray[:2]) == 2
    assert len(docarray[:3]) == 3
    assert len(docarray[:100]) == 3

    assert len(docarray[1:]) == 2
    assert len(docarray[2:]) == 1
    assert len(docarray[3:]) == 0
    assert len(docarray[100:]) == 0


def test_array_get_fail(docarray, document_factory):
    with pytest.raises(IndexError):
        docarray[0.1] = 1  # Set fail, not a supported type
    with pytest.raises(IndexError):
        docarray[0.1]  # Get fail, not a supported type


def test_docarray_init(docs, docarray):
    # we need low-level protobuf generation for testing
    assert len(docs) == len(docarray)
    for d, od in zip(docs, docarray):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text


def test_docarray_iterate_twice(docarray):
    j = 0
    for _ in docarray:
        for _ in docarray:
            j += 1
    assert j == len(docarray) ** 2


def test_docarray_reverse(docs, docarray):
    ids = [d.id for d in docs]
    docarray.reverse()
    ids2 = [d.id for d in docarray]
    assert list(reversed(ids)) == ids2


def test_match_chunk_array():
    with Document() as d:
        d.content = 'hello world'

    m = Document()
    d.matches.append(m)
    assert m.granularity == d.granularity
    assert m.adjacency == 0
    assert d.matches[0].adjacency == d.adjacency + 1
    assert len(d.matches) == 1

    c = Document()
    d.chunks.append(c)
    assert c.granularity == 0
    assert d.chunks[0].granularity == d.granularity + 1
    assert c.adjacency == d.adjacency
    assert len(d.chunks) == 1


def add_chunk(doc):
    with Document() as chunk:
        chunk.granularity = doc.granularity + 1
        chunk.adjacency = doc.adjacency
        doc.chunks.append(chunk)
        return chunk


def add_match(doc):
    with Document() as match:
        match.granularity = doc.granularity
        match.adjacency = doc.adjacency + 1
        doc.matches.append(match)
        return match
