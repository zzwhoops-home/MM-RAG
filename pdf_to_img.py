# this requires poppler, check https://pypi.org/project/pdf2image/
import pdf2image
from tqdm import tqdm
from pathlib import Path
from typing import Any
import uuid

def pdf_to_img(fp: Path, output: Path, fmt: str = "png", threads: int = 1) -> Any:
    """Converts a PDF to an output folder of images

    Args:
        fp (Path): the path of the input PDF
        output (Path): the output folder of images
        fmt (str): the type of image to output. Defaults to "png"
        threads (int): the number of threads to use in conversion. Defaults to 1

    Returns:
        Any: _description_
    """
    # create appropriate folder & subfolders if needed
    if not output.exists():
        output.mkdir(parents=True, exist_ok=True)

    uuid5 = str(uuid.uuid5(
        namespace=uuid.NAMESPACE_OID,
        name=fp.name, # get only the last part (e.g. path_to_file/test.pdf becomes `test.pdf`)
    ))

    # get the ending 12-digit section of the uuid5
    img_id = uuid5.split("-")[-1]
    img_dir = output / img_id

    try:
        img_dir.mkdir(parents=True, exist_ok=False)
    except Exception as e:
        print(f"Hashing conflict, {img_dir} already exists in your output directory {output}")

    try:
        pdf2image.convert_from_path(
            pdf_path=fp,
            output_folder=img_dir,
            output_file=img_id,
            dpi=200,
            fmt=fmt,
            thread_count=threads,
        )
    except Exception as e:
        print(f"Conversion failed. Error: {e}")

# def pdf_to_img_bulk(fp)

if __name__ == "__main__":
    # .../MM-RAG
    output = Path.cwd() / "output" / "test"

    fp = Path("C:/Users/zd/Desktop/GitHub/MM-RAG/data/Alignment Index Details.pdf")
    pdf_to_img(
        fp=fp,
        output=output,
        threads=12
    )