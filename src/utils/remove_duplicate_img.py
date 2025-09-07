import os
import json

if __name__ == "__main__":
    img_container_dir = (
        "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/src/repositories/images"
    )
    product_path = "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/products.json"

    products = []
    with open(product_path, "r") as f:
        products = json.load(f)

    pids = [product.get("pid") for product in products]
    img_dirs = os.listdir(img_container_dir)

    set_pids = set(pids)
    set_img_dirs = set(img_dirs)

    print(set_img_dirs.difference(set_pids))
