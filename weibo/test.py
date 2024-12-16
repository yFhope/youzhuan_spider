from urllib.parse import unquote, unquote_plus

decoded_url = unquote("https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D61%26q%3D%E9%AB%98%E6%A4%85%E5%B2%AD%26t%3D&page_type=searchall&page=11")
print(decoded_url)  # 输出: https://example.com/path to/resource

decoded_query = unquote_plus("containerid=100103type%3D61%26q%3D高椅岭%26t%3D&page_type=searchall&page=11")
print(decoded_query)  # 输出: search query with spaces


from urllib.parse import quote, quote_plus

# 对普通字符串进行URL编码
original_string = decoded_query
encoded_string = quote(original_string)
print("Encoded:", encoded_string)

# 对包含空格的字符串进行URL编码，并将空格转换为加号
string_with_spaces = decoded_query
encoded_string_plus = quote_plus(string_with_spaces)
print("Encoded with plus:", encoded_string_plus)