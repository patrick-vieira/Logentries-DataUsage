
def print_response(response):
    header = build_header(response)
    return header


def build_header(header_data):
    return "{}".format(header_data)


def build_products(products_data):
    return "{}".format(products_data)


def get_products(nf_data):
    header = build_header(nf_data[0])
    products = build_products(nf_data[2])
    total = build_products(nf_data[3])

    html = "{}<br>{}<br>{}".format(header, products, total)

    return html
