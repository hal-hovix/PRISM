# テストガイド

## 概要

PRISMシステムの包括的なテストスイートとテスト実行方法について説明します。

**バージョン**: 2.0.0  
**更新日**: 2025年1月27日

## テスト構成

### テストディレクトリ構造

```
tests/
├── fixtures/
│   └── conftest.py          # 共通フィクスチャ
├── unit/
│   ├── test_api_routers.py  # APIルーターのテスト
│   └── test_async_processing.py # 非同期処理のテスト
├── integration/
│   └── test_integration.py  # 統合テスト
└── performance/
    └── test_performance.py  # パフォーマンステスト
```

### テストタイプ

1. **単体テスト (Unit Tests)**
   - 個別の関数・クラスのテスト
   - モックを使用した独立したテスト
   - 高速実行

2. **統合テスト (Integration Tests)**
   - 複数コンポーネント間の連携テスト
   - 実際のAPIエンドポイントのテスト
   - データベース連携テスト

3. **非同期テスト (Async Tests)**
   - 非同期処理のテスト
   - バッチ処理・並行処理のテスト
   - キャッシュ機能のテスト

4. **パフォーマンステスト (Performance Tests)**
   - 負荷テスト
   - レスポンス時間の測定
   - リソース使用量の監視

## テスト実行

### 1. 基本的なテスト実行

```bash
# 全テスト実行
python tools/run_tests.py

# 特定のテストタイプ
python tools/run_tests.py --type unit
python tools/run_tests.py --type integration
python tools/run_tests.py --type async
python tools/run_tests.py --type performance
```

### 2. カバレッジ付きテスト実行

```bash
# カバレッジレポート生成
python tools/run_tests.py --coverage

# カバレッジレポート確認
open htmlcov/index.html
```

### 3. 詳細なテスト実行

```bash
# 詳細出力
python tools/run_tests.py --verbose

# 全チェック実行（テスト・リンティング・セキュリティ）
python tools/run_tests.py --all
```

### 4. 個別テスト実行

```bash
# pytest直接実行
python -m pytest tests/unit/test_api_routers.py -v

# 特定のテスト関数
python -m pytest tests/unit/test_api_routers.py::TestHealthRouter::test_health_check -v
```

## テスト設定

### pytest設定 (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests", "src"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "async: Async tests",
    "slow: Slow tests",
    "api: API tests",
    "notion: Notion API tests",
    "cache: Cache tests",
    "performance: Performance tests"
]
asyncio_mode = "auto"
```

### テストマーカー

```python
@pytest.mark.unit
def test_basic_function():
    """単体テスト"""
    pass

@pytest.mark.integration
def test_api_integration():
    """統合テスト"""
    pass

@pytest.mark.async
@pytest.mark.asyncio
async def test_async_processing():
    """非同期テスト"""
    pass

@pytest.mark.performance
def test_performance():
    """パフォーマンステスト"""
    pass
```

## テストフィクスチャ

### 共通フィクスチャ

```python
@pytest.fixture
def test_client():
    """FastAPIテストクライアント"""
    from src.api.main import app
    return TestClient(app)

@pytest.fixture
async def async_test_client():
    """非同期テストクライアント"""
    from src.api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_notion_client():
    """モックNotionクライアント"""
    mock = Mock()
    mock.fetch_pages_async = AsyncMock(return_value=[])
    return mock
```

### テストデータフィクスチャ

```python
@pytest.fixture
def sample_notion_page():
    """サンプルNotionページデータ"""
    return {
        "id": "test-page-id",
        "properties": {
            "タイトル": {
                "title": [{"text": {"content": "テストタスク"}}]
            }
        }
    }
```

## テストベストプラクティス

### 1. テスト命名規則

```python
def test_function_name_should_return_expected_result():
    """テスト関数名は期待する結果を明確に表現"""
    pass

def test_function_name_with_invalid_input_should_raise_error():
    """エラーケースのテスト"""
    pass
```

### 2. テスト構造 (AAA Pattern)

```python
def test_classify_item():
    # Arrange - テストデータの準備
    item = {"title": "テストアイテム", "content": "テストコンテンツ"}
    expected_category = "Task"
    
    # Act - テスト対象の実行
    result = classify_item(item)
    
    # Assert - 結果の検証
    assert result["category"] == expected_category
    assert result["confidence"] > 0.8
```

### 3. モックの使用

```python
@patch('src.api.routers.classify.classify_with_plugins')
def test_classify_endpoint(mock_classify):
    # モックの設定
    mock_classify.return_value = {
        "category": "Task",
        "confidence": 0.95
    }
    
    # テスト実行
    response = test_client.post("/classify", json={"items": [item]})
    
    # 検証
    assert response.status_code == 200
    mock_classify.assert_called_once()
```

### 4. 非同期テスト

```python
@pytest.mark.asyncio
async def test_async_processing():
    # 非同期処理のテスト
    result = await async_function()
    assert result is not None
```

## 継続的インテグレーション

### GitHub Actions でのテスト実行

```yaml
# .github/workflows/ci-cd.yml
- name: Run Tests
  run: |
    python tools/run_tests.py --all
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### テスト結果の確認

1. **GitHub Actions**: 各プルリクエストでテスト結果を確認
2. **ローカル実行**: `python tools/run_tests.py --all`
3. **カバレッジレポート**: `htmlcov/index.html`

## トラブルシューティング

### よくある問題

**問題**: テストが失敗する
```bash
# 解決方法
python tools/run_tests.py --verbose  # 詳細ログ確認
python -m pytest tests/unit/test_api_routers.py::TestHealthRouter::test_health_check -v -s
```

**問題**: 非同期テストが失敗する
```bash
# 解決方法
pip install pytest-asyncio
python -m pytest tests/unit/test_async_processing.py -v
```

**問題**: モックが正しく動作しない
```bash
# 解決方法
# インポートパスを確認
# モックの設定を確認
```

### デバッグ方法

```python
# デバッグ出力
import logging
logging.basicConfig(level=logging.DEBUG)

# テスト内でのデバッグ
def test_debug():
    print("Debug info:", variable)
    import pdb; pdb.set_trace()  # ブレークポイント
```

## 参考資料

- [pytest ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio ドキュメント](https://pytest-asyncio.readthedocs.io/)
- [FastAPI テストドキュメント](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock ドキュメント](https://docs.python.org/3/library/unittest.mock.html)
