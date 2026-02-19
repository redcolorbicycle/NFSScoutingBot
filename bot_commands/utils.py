import random
import os
from io import BytesIO

import discord
import matplotlib.pyplot as plt

from bot_commands.constants import ASSETS, PR_COLORS, ROWS_PER_PAGE


async def send_asset(ctx, key: str) -> None:
    """Send a random asset from the named asset group to a Discord channel."""
    paths = ASSETS[key]
    path = random.choice(paths)
    if not os.path.isfile(path):
        await ctx.send("File not found.")
        return
    await ctx.send(file=discord.File(path, filename=os.path.basename(path)))


def apply_pr_colors(cell_dict, pr_col_index: int, df) -> None:
    """Apply color formatting to PR column cells based on value thresholds."""
    for (row, col), cell in cell_dict.items():
        if col == pr_col_index and row > 0:
            try:
                pr_value = int(df.iloc[row - 1, pr_col_index])
                for threshold, color in PR_COLORS:
                    if pr_value <= threshold:
                        cell.set_facecolor(color)
                        break
            except (ValueError, IndexError):
                pass


def render_table_image(
    df,
    figwidth: float = 24,
    figheight_per_row: float = 0.5,
    fontsize: int = 10,
    dpi: int = None,
    pr_col_index: int = None,
) -> BytesIO:
    """Render a DataFrame as a styled matplotlib table and return a PNG BytesIO buffer."""
    fig, ax = plt.subplots(figsize=(figwidth, len(df) * figheight_per_row + 1))
    ax.axis("tight")
    ax.axis("off")
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.auto_set_column_width(col=list(range(len(df.columns))))

    cell_dict = table.get_celld()
    if pr_col_index is not None:
        apply_pr_colors(cell_dict, pr_col_index, df)

    for (row, col), cell in cell_dict.items():
        if row == 0 or col == 0:
            cell.set_text_props(weight="bold")

    row_height = 1 / len(df)
    for (row, col), cell in cell_dict.items():
        cell.set_height(row_height)

    buffer = BytesIO()
    save_kwargs = {"format": "png", "bbox_inches": "tight"}
    if dpi is not None:
        save_kwargs["dpi"] = dpi
    plt.savefig(buffer, **save_kwargs)
    buffer.seek(0)
    plt.close(fig)
    return buffer


async def send_paginated_table(ctx, df, rows_per_page: int = ROWS_PER_PAGE, **render_kwargs) -> None:
    """Send a DataFrame as one or more paginated table images to Discord."""
    total_pages = (len(df) + rows_per_page - 1) // rows_per_page
    for page in range(total_pages):
        df_page = df.iloc[page * rows_per_page:(page + 1) * rows_per_page]
        buffer = render_table_image(df_page, **render_kwargs)
        file = discord.File(fp=buffer, filename=f"table_page_{page + 1}.png")
        if total_pages > 1:
            await ctx.send(f"**Page {page + 1} of {total_pages}:**", file=file)
        else:
            await ctx.send(file=file)
        buffer.close()
