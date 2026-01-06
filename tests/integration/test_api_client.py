"""Integration tests for NotebookLM API client."""

import pytest
from pytest_httpx import HTTPXMock

from notebooklm import NotebookLMClient, Notebook, Source, Artifact
from notebooklm import AudioFormat, AudioLength, VideoFormat, VideoStyle
from notebooklm.auth import AuthTokens


@pytest.fixture
def auth_tokens():
    return AuthTokens(
        cookies={
            "SID": "test_sid",
            "HSID": "test_hsid",
            "SSID": "test_ssid",
            "APISID": "test_apisid",
            "SAPISID": "test_sapisid",
        },
        csrf_token="test_csrf_token",
        session_id="test_session_id",
    )


class TestClientInitialization:
    @pytest.mark.asyncio
    async def test_client_initialization(self, auth_tokens):
        async with NotebookLMClient(auth_tokens) as client:
            assert client._core.auth == auth_tokens
            assert client._core._http_client is not None

    @pytest.mark.asyncio
    async def test_client_context_manager_closes(self, auth_tokens):
        async with NotebookLMClient(auth_tokens) as client:
            http = client._core._http_client
        assert client._core._http_client is None

    @pytest.mark.asyncio
    async def test_client_raises_if_not_initialized(self, auth_tokens):
        client = NotebookLMClient(auth_tokens)
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.notebooks.list()


class TestListNotebooks:
    @pytest.mark.asyncio
    async def test_list_notebooks_returns_notebooks(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebooks = await client.notebooks.list()

        assert len(notebooks) == 2
        assert all(isinstance(nb, Notebook) for nb in notebooks)
        assert notebooks[0].title == "My First Notebook"
        assert notebooks[0].id == "nb_001"

    @pytest.mark.asyncio
    async def test_list_notebooks_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "wXbhsf" in str(request.url)
        assert b"f.req=" in request.content

    @pytest.mark.asyncio
    async def test_request_includes_cookies(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        cookie_header = request.headers.get("cookie", "")
        assert "SID=test_sid" in cookie_header
        assert "HSID=test_hsid" in cookie_header

    @pytest.mark.asyncio
    async def test_request_includes_csrf(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        mock_list_notebooks_response,
    ):
        httpx_mock.add_response(content=mock_list_notebooks_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.list()

        request = httpx_mock.get_request()
        body = request.content.decode()
        assert "at=test_csrf_token" in body


class TestCreateNotebook:
    @pytest.mark.asyncio
    async def test_create_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "CCqFvf",
            [
                "My Notebook",
                [],
                "new_nb_id",
                "📓",
                None,
                [None, None, None, None, None, [1704067200, 0]],
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.create("My Notebook")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "new_nb_id"
        assert notebook.title == "My Notebook"

    @pytest.mark.asyncio
    async def test_create_notebook_request_contains_title(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "CCqFvf",
            ["Test Title", [], "id", "📓", None, [None, None, None, None, None, [1704067200, 0]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.create("Test Title")

        request = httpx_mock.get_request()
        assert "CCqFvf" in str(request.url)


class TestGetNotebook:
    @pytest.mark.asyncio
    async def test_get_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [["source1"], ["source2"]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.get("nb_123")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "nb_123"
        assert notebook.title == "Test Notebook"

    @pytest.mark.asyncio
    async def test_get_notebook_uses_source_path(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "rLM1Ne",
            [["Name", [], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.get("nb_123")

        request = httpx_mock.get_request()
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)


class TestDeleteNotebook:
    @pytest.mark.asyncio
    async def test_delete_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("WWINqb", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.delete("nb_123")

        assert result is True


class TestAddSource:
    @pytest.mark.asyncio
    async def test_add_source_url(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "izAoDd",
            [
                [
                    [
                        ["source_id"],
                        "Example Site",
                        [None, 11, None, None, 5, None, 1, ["https://example.com"]],
                        [None, 2],
                    ]
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.add_url("nb_123", "https://example.com")

        assert isinstance(source, Source)
        assert source.id == "source_id"
        assert source.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_add_source_text(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "izAoDd", [[[["source_id"], "My Document", [None, 11], [None, 2]]]]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.add_text(
                "nb_123", "My Document", "This is the content"
            )

        assert isinstance(source, Source)
        assert source.id == "source_id"
        assert source.title == "My Document"


class TestStudioContent:
    @pytest.mark.asyncio
    async def test_generate_audio(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["src_001"], "Source 1", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=notebook_response.encode())

        audio_response = build_rpc_response(
            "R7cb6c", [["artifact_123", "Audio Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=audio_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_audio(notebook_id="nb_123")

        assert result is not None
        assert result.task_id == "artifact_123"
        assert result.status in ("pending", "in_progress", "processing")

        request = httpx_mock.get_requests()[-1]
        assert "R7cb6c" in str(request.url)

    @pytest.mark.asyncio
    async def test_generate_audio_with_format_and_length(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["src_001"], "Source 1", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=notebook_response.encode())

        response = build_rpc_response(
            "R7cb6c", [["artifact_123", "Audio Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_audio(
                notebook_id="nb_123",
                audio_format=AudioFormat.DEBATE,
                audio_length=AudioLength.LONG,
            )

        assert result is not None
        assert result.task_id == "artifact_123"

    @pytest.mark.asyncio
    async def test_generate_video_with_format_and_style(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        video_response = build_rpc_response(
            "R7cb6c", [["artifact_456", "Video Overview", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=video_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_video(
                notebook_id="nb_123",
                video_format=VideoFormat.BRIEF,
                video_style=VideoStyle.ANIME,
            )

        assert result is not None
        assert result.task_id == "artifact_456"

    @pytest.mark.asyncio
    async def test_generate_slide_deck(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        slide_deck_response = build_rpc_response(
            "R7cb6c", [["artifact_456", "Slide Deck", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=slide_deck_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_slide_deck(notebook_id="nb_123")

        assert result is not None
        assert result.task_id == "artifact_456"

    @pytest.mark.asyncio
    async def test_poll_studio_status(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "gArtLc", ["task_id_123", "completed", "https://audio.url"]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.poll_status(
                notebook_id="nb_123",
                task_id="task_id_123",
            )

        assert result is not None
        assert result.status == "completed"
        assert result.url == "https://audio.url"


class TestSummary:
    @pytest.mark.asyncio
    async def test_get_summary(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response(
            "VfAZjd", ["Summary of the notebook content..."]
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.notebooks.get_summary("nb_123")

        assert "Summary" in result


class TestRenameNotebook:
    @pytest.mark.asyncio
    async def test_rename_notebook(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # First response for rename (returns null)
        rename_response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=rename_response.encode())
        # Second response for get_notebook call after rename
        get_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "New Title",
                    [],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=get_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            notebook = await client.notebooks.rename("nb_123", "New Title")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "nb_123"
        assert notebook.title == "New Title"

    @pytest.mark.asyncio
    async def test_rename_notebook_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # Rename response (returns null)
        rename_response = build_rpc_response("s0tc2d", None)
        httpx_mock.add_response(content=rename_response.encode())
        # Get notebook response after rename
        get_response = build_rpc_response(
            "rLM1Ne",
            [["Renamed", [], "nb_123", "📘", None, [None, None, None, None, None, [1704067200, 0]]]],
        )
        httpx_mock.add_response(content=get_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.notebooks.rename("nb_123", "Renamed")

        request = httpx_mock.get_requests()[0]
        assert "s0tc2d" in str(request.url)
        assert "source-path=%2F" in str(request.url)


class TestDeleteSource:
    @pytest.mark.asyncio
    async def test_delete_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("tGMBJ", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.sources.delete("nb_123", "source_456")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_source_request_format(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("tGMBJ", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            await client.sources.delete("nb_123", "source_456")

        request = httpx_mock.get_request()
        assert "tGMBJ" in str(request.url)
        assert "source-path=%2Fnotebook%2Fnb_123" in str(request.url)


class TestGetSource:
    @pytest.mark.asyncio
    async def test_get_source(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        # get_source filters from get_notebook, so mock GET_NOTEBOOK response
        response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [
                        [["source_456"], "Source Title", [None, 0, [1704067200, 0]], [None, 2]],
                        [["source_789"], "Other Source", [None, 0, [1704153600, 0]], [None, 2]],
                    ],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            source = await client.sources.get("nb_123", "source_456")

        assert isinstance(source, Source)
        assert source.id == "source_456"
        assert source.title == "Source Title"


class TestGenerateQuiz:
    @pytest.mark.asyncio
    async def test_generate_quiz(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        quiz_response = build_rpc_response(
            "R7cb6c", [["quiz_123", "Quiz", "2024-01-05", None, 1]]
        )
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=quiz_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_quiz("nb_123")

        assert result is not None
        assert result.task_id == "quiz_123"


class TestDeleteStudioContent:
    @pytest.mark.asyncio
    async def test_delete_studio_content(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        response = build_rpc_response("V5N4be", [True])
        httpx_mock.add_response(content=response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.delete("nb_123", "task_id_123")

        assert result is True


class TestMindMap:
    @pytest.mark.asyncio
    async def test_generate_mind_map(
        self,
        auth_tokens,
        httpx_mock: HTTPXMock,
        build_rpc_response,
    ):
        notebook_response = build_rpc_response(
            "rLM1Ne",
            [
                [
                    "Test Notebook",
                    [[["source_123"], "Source", [None, 0], [None, 2]]],
                    "nb_123",
                    "📘",
                    None,
                    [None, None, None, None, None, [1704067200, 0]],
                ]
            ],
        )
        mindmap_response = build_rpc_response("yyryJe", None)
        httpx_mock.add_response(content=notebook_response.encode())
        httpx_mock.add_response(content=mindmap_response.encode())

        async with NotebookLMClient(auth_tokens) as client:
            result = await client.artifacts.generate_mind_map("nb_123")

        # Mind map returns dict or None
        assert result is None or isinstance(result, dict)
