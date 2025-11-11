from tools.search_tools import search_content_examples

# Test WITHOUT platform filter - should search ALL 700+ posts
result = search_content_examples(
    query="writing tips advice",
    platform=None,
    match_count=10
)

print(result)
