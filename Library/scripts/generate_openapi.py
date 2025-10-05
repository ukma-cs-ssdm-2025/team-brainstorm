import yaml
from pathlib import Path
from src.api.main import app

def main():
    spec = app.openapi()
    out = Path("docs/api/openapi-generated.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True)
    print("✅ OpenAPI YAML збережено в", out)

if __name__ == "__main__":
    main()
