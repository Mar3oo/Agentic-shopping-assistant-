from __future__ import annotations

import streamlit as st


def _format_price(product: dict) -> str:
    price_text = product.get("price_text")
    if price_text:
        return str(price_text)

    price = product.get("price")
    if price in (None, ""):
        return "Price unavailable"

    currency = product.get("currency")
    if currency:
        return f"{currency} {price}"
    return str(price)


def render_product_cards(products: list[dict], *, title: str = "Products") -> None:
    st.subheader(title)
    if not products:
        st.info("No products available.")
        return

    columns = st.columns(2)
    for index, product in enumerate(products):
        column = columns[index % 2]
        with column:
            st.markdown(f"### {product.get('title') or 'Unnamed product'}")
            st.write(f"**Price:** {_format_price(product)}")

            source = product.get("source")
            if source:
                st.caption(f"Source: {source}")

            details = product.get("details_text")
            if details:
                st.write(str(details)[:280])

            link = product.get("link")
            if link:
                st.markdown(f"[Open product]({link})")
            st.markdown("---")
