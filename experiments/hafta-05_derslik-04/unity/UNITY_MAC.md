# Derslik 4: Unity'de açma (Mac)

Dosya: `derslik4_1440big_unity.ply`. Birim metre, Y yukarı, zemin y = 0, orijin salon zemininin ortası,
X uzun kenar. Unity'nin sol el sistemine çevrildi; GameObject dönüşümü sıfır bırakılır.
1.046.528 Gaussian (salon dışına uçuşan %6 atıldı), ~260 MB. Salon yaklaşık X −12…+9 m, Z −9…+7 m,
tavan ızgarası ~3,3 m, tavan ~4,1 m. Ölçek 207,2 cm/birim (3 ölçünün uydurması, ±%7 belirsizlik).
Kontrol görseli: `kontrol_unity_ply.png`.

## 1. Kurulum (bir kez)
1. Unity Hub → Unity 2022.3 LTS ya da Unity 6, **3D (Built-in)** şablonuyla yeni proje.
   URP kullanılacaksa 4. adımdaki ek ayar gerekir.
2. Window → Package Manager → `+` → *Add package from git URL* →
   `https://github.com/aras-p/UnityGaussianSplatting.git?path=package`
3. Mac'te grafik API'si Metal olmalı (varsayılan). Project Settings → Player → Other Settings →
   Auto Graphics API açık kalsın.

## 2. İçe aktarma
1. `derslik4_1440big_unity.ply` dosyasını projenin dışında bir klasöre koyun
   (Assets içine koymak gerekmez).
2. Tools → Gaussian Splats → **Create GaussianSplatAsset**
   - Input PLY File: dosyayı seçin.
   - Quality: **Very High** (en az kayıp). Bellek yetmezse High.
   - Create Asset. Asset `Assets/GaussianAssets/` altına yazılır; 1–2 dk sürebilir.

## 3. Sahneye koyma
1. Hierarchy → Create Empty → adı `Derslik4`. Position, rotation (0, 0, 0), scale (1, 1, 1).
2. Add Component → **Gaussian Splat Renderer** → Asset alanına oluşan asset'i sürükleyin.
3. Main Camera: Position (0, 1.6, 0) göz hizası. Scene görünümünde gezinmek için sağ tık + WASD.

## 4. URP kullanıyorsanız
URP Renderer asset'ine *Add Renderer Feature* → **Gaussian Splat URP Feature** ekleyin.

## 5. Kontroller
- **Ayna görüntüsü kontrolü:** beyaz tahtadaki yazı ve Atatürk portresi düz okunmalı. Ters (aynalı)
  görünürse `Derslik4` Scale Z = −1 yapın.
- **Ölçek:** sahneye 1×1×1 küp koyun (1 m). Kapı ~2,07 m, masa platformdan ~0,74 m, platform ~0,41 m.
- Zemin y = 0'da, öğretmen platformu y ≈ 0,41 m'de olmalı.
- Gaussian'lar sahnenin dışına taşıyorsa ya da her şey yan yatmışsa dönüşümü değiştirmeden bana haber verin.

## 6. VR notu
VR testi Mac'te yapılamaz; PC'ye bağlı bir VR gözlükle yapılmalı. 1,1 M Gaussian, gözlüğün kendi işlemcisiyle
(bağımsız) çalıştırmak için ağır; gerekirse Quality = Medium/Low ya da Gaussian sayısı azaltılmış bir sürüm hazırlanır.
