from autodata.tools.web import get_page_content, find_pdf_links, download_pdf, extract_text_from_pdf, extract_keywords

url = "https://mst.gov.vn/van-ban-phap-luat/du-thao/2256.htm"
html = get_page_content(url)
links = find_pdf_links(html, url)
print("pdf links:", links)
if links:
    pdf_url = links[0]
    download_pdf(pdf_url, "test_output/draft.pdf")
    text = extract_text_from_pdf("test_output/draft.pdf")
    kws = extract_keywords(text, top_n=12)
    print("keywords:", kws)
