from PIL import Image
import os


def create_ico():
    # Caminho da sua imagem base de alta resolução
    png_path = os.path.join("assets", "icon.png")
    ico_path = os.path.join("assets", "icon.ico")

    if os.path.exists(png_path):
        img = Image.open(png_path)
        # O Windows recomenda esses tamanhos padrão para ícones de sistema
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, sizes=icon_sizes)
        print(f"✅ Ícone GRC gerado com sucesso em: {ico_path}")
    else:
        print("❌ Erro: assets/icon.png não encontrado.")


if __name__ == "__main__":
    create_ico()