import io
import zipfile

from . import config

_META = {"manifest.xml", "transfer.xml", "directives.xml", "mimetype"}


def download_meca(s3_key: str) -> bytes:
    s3 = config.s3_client()
    obj = s3.get_object(Bucket=config.BUCKET, Key=s3_key, **config.REQUESTER_PAYS)
    return obj["Body"].read()


def extract_jats(meca_bytes: bytes) -> str:
    """Return the JATS XML text from a .meca zip (the content/*.xml article file)."""
    with zipfile.ZipFile(io.BytesIO(meca_bytes)) as z:
        candidates = [
            n for n in z.namelist()
            if n.lower().endswith(".xml") and n.rsplit("/", 1)[-1] not in _META
        ]
        # Prefer content/*.xml; pick the largest (the article body, not a stub).
        candidates.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
        if not candidates:
            raise ValueError("no JATS article XML found in .meca")
        return z.read(candidates[0]).decode("utf-8", "ignore")
