-- 潮汕文化宣传平台 — 非遗/民俗活动 经纬度种子数据
-- 基于实际地理位置的手工录入，偏差 < 500m（地图尺度可接受）
-- 使用方法: mysql -u root -p chaoshan_platform < seed_coordinates.sql

USE chaoshan_platform;

-- ============================================================
-- 非遗项目坐标 (10 条)
-- ============================================================

UPDATE heritages SET latitude = 23.6650, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '潮州音乐';
UPDATE heritages SET latitude = 23.2650, longitude = 116.6100, address = '广东省汕头市潮阳区' WHERE name = '英歌舞';
UPDATE heritages SET latitude = 23.6680, longitude = 116.6450, address = '广东省潮州市湘桥区牌坊街' WHERE name = '潮剧';
UPDATE heritages SET latitude = 23.6650, longitude = 116.6420, address = '广东省潮州市湘桥区' WHERE name = '潮汕工夫茶';
UPDATE heritages SET latitude = 23.6700, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '嵌瓷';
UPDATE heritages SET latitude = 23.6660, longitude = 116.6450, address = '广东省潮州市湘桥区' WHERE name = '潮汕木雕';
UPDATE heritages SET latitude = 23.6670, longitude = 116.6430, address = '广东省潮州市湘桥区' WHERE name = '铁枝木偶';
UPDATE heritages SET latitude = 23.6600, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '潮汕剪纸';
UPDATE heritages SET latitude = 23.6650, longitude = 116.6380, address = '广东省潮州市湘桥区' WHERE name = '潮州大锣鼓';
UPDATE heritages SET latitude = 23.3000, longitude = 116.1700, address = '广东省揭阳市普宁市' WHERE name = '普宁英歌';

-- ============================================================
-- 民俗活动坐标 (8 条)
-- ============================================================

UPDATE folk_events SET latitude = 23.4700, longitude = 116.7700, address = '广东省汕头市澄海区' WHERE name = '营老爷巡游';
UPDATE folk_events SET latitude = 23.6680, longitude = 116.6450, address = '广东省潮州市湘桥区牌坊街' WHERE name = '元宵灯会';
UPDATE folk_events SET latitude = 23.3500, longitude = 116.6800, address = '广东省汕头市金平区海滨路' WHERE name = '端午节赛龙舟';
UPDATE folk_events SET latitude = 23.6650, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '出花园';
UPDATE folk_events SET latitude = 23.6700, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '中秋烧塔';
UPDATE folk_events SET latitude = 23.6650, longitude = 116.6400, address = '广东省潮州市湘桥区' WHERE name = '冬至祭祖';
UPDATE folk_events SET latitude = 23.2650, longitude = 116.6100, address = '广东省汕头市潮阳区' WHERE name = '游神赛会';
UPDATE folk_events SET latitude = 23.3550, longitude = 116.6750, address = '广东省汕头市金平区小公园' WHERE name = '潮汕侨批文化展';
