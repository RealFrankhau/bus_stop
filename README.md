# 香港巴士站地圖

一個顯示全港巴士站位置的互動地圖網頁應用程式，使用 Leaflet.js 及政府官方地圖圖層。

## 功能特色

- 顯示全港 **9,330+** 個巴士站位置（KMB、CTB、LWB）
- 使用政府官方地圖圖層（地政處地圖 + 中文標籤）
- 按一下巴士站顯示詳細資料：
  - 站號（stop_id，使用各巴士公司 API 本身的站號格式）
  - 巴士站名
  - 所屬巴士公司（KMB / CTB / LWB）
  - 所有途經該站的巴士路線
- 同一 GPS 位置有多個巴士站時，合併顯示並以較大圓點標示
- 全頁使用 Huninn 字型
- 載入進度指示器

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `index.html` | 主網頁，直接以瀏覽器開啟即可使用 |
| `bus_stops.json` | 巴士站資料（約 1.7MB），包含站號、座標、名稱、公司及路線 |
| `build_stops.py` | 用於重新產生 `bus_stops.json` 的 Python 腳本 |

## 資料來源

| 公司 | API 來源 | 站號格式 |
|------|----------|----------|
| KMB / 龍運 | https://data.etabus.gov.hk/v1/transport/kmb/stop | 16 位十六進位（如 `18492910339410B1`） |
| CTB | https://rt.data.gov.hk/v1/transport/citybus-nwfb/stop/{stop_id} | 6 位數字（如 `002188`） |

路線資料來源：
- KMB/LWB：https://data.etabus.gov.hk/v1/transport/kmb/route-stop
- CTB：https://rt.data.gov.hk/v2/transport/citybus/route-stop/ctb/{route}/{direction}

## 使用方法

### 基本使用

1. Clone 或下載此 repository
2. 用瀏覽器開啟 `index.html`
3. 等待巴士站資料載入完成
4. 放大地圖並按一下圓點查看巴士站詳情

> **注意**：由於瀏覽器 CORS 限制，直接開啟 `index.html` 時，`bus_stops.json` 需與 `index.html` 在同一目錄下。如果遇到載入問題，可使用本地伺服器：
> ```bash
> python -m http.server 8000
> # 然後訪問 http://localhost:8000
> ```

### 更新巴士站資料

巴士路線和站點會因應實際營運情況變動，建議定期更新：

```bash
python build_stops.py
```

執行時間約 3-5 分鐘，完成後會自動更新 `bus_stops.json`。

## 自動更新（GitHub Actions）

Repository 已包含 GitHub Actions workflow，可每 3 個月自動更新一次。

### 設定步驟

1. 將此 repository 推到 GitHub
2. GitHub Actions 會根據 `.github/workflows/` 內的設定自動執行
3. 執行時間：每年 1 月、4 月、7 月、10 月的第一天（UTC 時間 00:00）
4. 如有資料變更，會自動 commit 並 push

### 手動觸發更新

在 GitHub repository 的 **Actions** 分頁中，選擇 **Update Bus Stops** workflow，點選 **Run workflow** 即可手動觸發更新。

## 地圖圖層

- **底圖**：香港政府地政處地圖（WGS84）
- **標籤**：中文地名標籤圖層
- 圖層來源：https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/

## 技術堆疊

- **前端**：原生 HTML/CSS/JavaScript
- **地圖庫**：Leaflet.js 1.9.4
- **字型**：Huninn（Google Fonts）
- **資料格式**：JSON
- **自動化**：GitHub Actions

## 資料統計

- 總巴士站數：9,330
- KMB 站：6,136
- LWB 站：869
- CTB 站：2,574
- 同一 GPS 位置有多個站的 location：699

## 免責聲明

- 巴士站資料來源於香港政府開放數據平台（data.gov.hk / etabus.gov.hk）
- 資料僅供參考，實際營運情況請以各巴士公司官方公布為準
- 地圖圖層版權歸香港特別行政區政府所有

## License

MIT
