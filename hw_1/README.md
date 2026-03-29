# EC581 HW1 - BIST100 Consecutive Return Strategies

Bu klasörde BIST100 (`^XU100`) için iki adet `backtrader` stratejisi modüler biçimde hazırlanmıştır:

- `TrendFollowingStrategy`: `n` ardışık pozitif günden sonra al, `m` ardışık negatif günden sonra sat
- `MeanReversionStrategy`: `n` ardışık negatif günden sonra al, `m` ardışık pozitif günden sonra sat

Not:
Yahoo Finance tarafında `^XU100` günlük veri bazı dönemlerde boş dönebiliyor. Script bu durumda otomatik olarak `XU100.IS` sembolünü dener ve kullanılan sembolü terminal çıktısında gösterir.

## Dosya Yapısı

- `config.py`: genel backtest ayarları
- `data.py`: `yfinance` veri indirme ve günlük getiri hesaplama
- `strategies.py`: iki strateji sınıfı ve ortak temel sınıf
- `engine.py`: `Cerebro` kurulum ve strateji çalıştırma fonksiyonları
- `reporting.py`: analyzer özetleri ve CSV çıktıları
- `plots.py`: performans ve sinyal grafikleri
- `run_backtests.py`: komut satırı giriş noktası

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r hw_1/requirements.txt
python -m ipykernel install --user --name ec581-hw1 --display-name "Python (ec581-hw1)"
```

## Çalıştırma

```bash
source .venv/bin/activate
python -m hw_1.run_backtests
```

Örnek parametrik çalıştırma:

```bash
python -m hw_1.run_backtests \
  --start 2015-01-01 \
  --trend-entry 4 \
  --trend-exit 2 \
  --mean-entry 3 \
  --mean-exit 1
```

İstersen özel bir etiket de verebilirsin:

```bash
python -m hw_1.run_backtests \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --label long_sample
```

Çıktılar varsayılan olarak `hw_1/output/` altında kaydedilir:

- Her koşu için ayrı bir alt klasör açılır
- Klasör adı seçilen tarih ve `n/m` parametrelerinden otomatik üretilir
- Dosya adları da aynı etiketle başlar

Örnek çıktı yolu:

```text
hw_1/output/start_1997-07-01__end_2026-03-27__trend_n3_m2__mean_n3_m2/
```

Bu klasörde ayrıca her strateji için sinyal günlüğü de oluşur:

- `..._trend_following_signals.csv`
- `..._mean_reversion_signals.csv`
- `..._signal_report.md`

Bu dosyalarda şunlar yer alır:

- sinyalin geldiği tarih
- sinyalin nedeni
- ardından gerçekleşen alım veya satım tarihi ve fiyatı
- işlem kapanınca oluşan net PnL ve geri dönütü (`positive`, `negative`, `flat`)


python -m hw_1.run_backtests \
  --start 2024-01-01 \
  --end 2026-03-27 \
  --trend-entry 3 \
  --trend-exit 2 \
  --mean-entry 4 \
  --mean-exit 1

python -m hw_1.run_backtests \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --trend-entry 3 \
  --trend-exit 2 \
  --mean-entry 4 \
  --mean-exit 1


python -m hw_1.optimize_strategies \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --n-min 1 \
  --n-max 10 \
  --m-min 1 \
  --m-max 10 \
  --objective sharpe_ratio


python -m hw_1.optimize_hybrid_strategy \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --n-min 1 \
  --n-max 10 \
  --m-min 1 \
  --m-max 10 \
  --trend-periods 200 \
  --objective sharpe_ratio

python -m hw_1.run_hybrid_backtest \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --entry-run 1 \
  --exit-run 4 \
  --trend-period 100