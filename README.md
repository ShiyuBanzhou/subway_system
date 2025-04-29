## 数据库创建和数据插入
```sql
-- --------------------------------------------------
-- Subway Information System Database Setup Script
-- --------------------------------------------------

-- 1. 创建数据库 (如果不存在)
CREATE DATABASE IF NOT EXISTS `subway_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `subway_system`;

-- --------------------------------------------------
-- 表结构 `Line`
-- --------------------------------------------------
DROP TABLE IF EXISTS `Schedule`;
DROP TABLE IF EXISTS `Ticket`;
DROP TABLE IF EXISTS `Train`;
DROP TABLE IF EXISTS `Station`;
DROP TABLE IF EXISTS `Passenger`;
DROP TABLE IF EXISTS `Line`;

CREATE TABLE `Line` (
  `line_id` int NOT NULL AUTO_INCREMENT COMMENT '线路ID',
  `line_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '线路名称',
  `start_station_id` int DEFAULT NULL COMMENT '首发站ID (逻辑关联)',
  `end_station_id` int DEFAULT NULL COMMENT '终点站ID (逻辑关联)',
  `status` enum('运营','停运') COLLATE utf8mb4_unicode_ci DEFAULT '运营' COMMENT '状态',
  `open_date` date DEFAULT NULL COMMENT '开通日期',
  PRIMARY KEY (`line_id`),
  UNIQUE KEY `uq_line_name` (`line_name`) -- 唯一约束 (类型1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地铁线路信息表';

-- --------------------------------------------------
-- 表结构 `Station`
-- --------------------------------------------------
CREATE TABLE `Station` (
  `station_id` int NOT NULL AUTO_INCREMENT COMMENT '站点ID',
  `station_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '站点名称',
  `line_id` int NOT NULL COMMENT '所属线路ID',
  `location_desc` text COLLATE utf8mb4_unicode_ci COMMENT '站点位置描述',
  `is_transfer` tinyint(1) DEFAULT '0' COMMENT '是否换乘站 (0:否, 1:是)',
  PRIMARY KEY (`station_id`),
  UNIQUE KEY `uq_station_name_line` (`station_name`, `line_id`) COMMENT '同一线路下站点名唯一', -- 复合唯一约束 (类型1 变种)
  KEY `fk_station_line` (`line_id`), -- 外键索引
  CONSTRAINT `fk_station_line` FOREIGN KEY (`line_id`) REFERENCES `Line` (`line_id`) ON DELETE CASCADE ON UPDATE CASCADE -- 外键约束 (类型2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地铁站点信息表';

-- --------------------------------------------------
-- 表结构 `Train`
-- --------------------------------------------------
CREATE TABLE `Train` (
  `train_id` int NOT NULL AUTO_INCREMENT COMMENT '列车ID',
  `train_number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '列车编号',
  `line_id` int NOT NULL COMMENT '所属线路ID',
  `model` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '列车型号',
  `capacity` int DEFAULT NULL COMMENT '容量',
  `status` enum('运行中','维修中') COLLATE utf8mb4_unicode_ci DEFAULT '运行中' COMMENT '状态',
  PRIMARY KEY (`train_id`),
  UNIQUE KEY `uq_train_number` (`train_number`), -- 唯一约束 (类型1)
  KEY `fk_train_line` (`line_id`), -- 外键索引
  CONSTRAINT `fk_train_line` FOREIGN KEY (`line_id`) REFERENCES `Line` (`line_id`) ON DELETE RESTRICT ON UPDATE CASCADE -- 外键约束 (类型2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地铁列车信息表';

-- --------------------------------------------------
-- 表结构 `Passenger`
-- --------------------------------------------------
CREATE TABLE `Passenger` (
  `passenger_id` int NOT NULL AUTO_INCREMENT COMMENT '乘客ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '姓名', -- 非空约束 (类型3)
  `phone_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `registration_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '注册日期',
  PRIMARY KEY (`passenger_id`),
  UNIQUE KEY `uq_phone_number` (`phone_number`) -- 唯一约束 (类型1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='乘客信息表';

-- --------------------------------------------------
-- 表结构 `Ticket`
-- --------------------------------------------------
CREATE TABLE `Ticket` (
  `ticket_id` int NOT NULL AUTO_INCREMENT COMMENT '票务ID',
  `passenger_id` int NOT NULL COMMENT '乘客ID',
  `purchase_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
  `departure_station_id` int NOT NULL COMMENT '出发站点ID',
  `arrival_station_id` int NOT NULL COMMENT '到达站点ID',
  `price` decimal(10,2) NOT NULL COMMENT '票价',
  `payment_status` enum('已支付','未支付') COLLATE utf8mb4_unicode_ci DEFAULT '已支付' COMMENT '支付状态',
  PRIMARY KEY (`ticket_id`),
  KEY `fk_ticket_passenger` (`passenger_id`), -- 外键索引
  KEY `fk_ticket_dep_station` (`departure_station_id`), -- 外键索引
  KEY `fk_ticket_arr_station` (`arrival_station_id`), -- 外键索引
  CONSTRAINT `fk_ticket_passenger` FOREIGN KEY (`passenger_id`) REFERENCES `Passenger` (`passenger_id`) ON DELETE CASCADE ON UPDATE CASCADE, -- 外键约束 (类型2)
  CONSTRAINT `fk_ticket_dep_station` FOREIGN KEY (`departure_station_id`) REFERENCES `Station` (`station_id`) ON DELETE RESTRICT ON UPDATE CASCADE, -- 外键约束 (类型2)
  CONSTRAINT `fk_ticket_arr_station` FOREIGN KEY (`arrival_station_id`) REFERENCES `Station` (`station_id`) ON DELETE RESTRICT ON UPDATE CASCADE, -- 外键约束 (类型2)
  CONSTRAINT `chk_price` CHECK ((`price` > 0)) -- CHECK约束 (类型4)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='票务信息表';

-- --------------------------------------------------
-- 表结构 `Schedule`
-- --------------------------------------------------
CREATE TABLE `Schedule` (
  `schedule_id` int NOT NULL AUTO_INCREMENT COMMENT '时刻表ID',
  `train_id` int NOT NULL COMMENT '列车ID',
  `station_id` int NOT NULL COMMENT '站点ID',
  `arrival_time` time DEFAULT NULL COMMENT '预计到达时间',
  `departure_time` time DEFAULT NULL COMMENT '预计出发时间',
  `schedule_date` date NOT NULL COMMENT '日期',
  PRIMARY KEY (`schedule_id`),
  UNIQUE KEY `uq_train_station_date` (`train_id`,`station_id`,`schedule_date`), -- 复合唯一约束 (类型1 变种)
  KEY `fk_schedule_train` (`train_id`), -- 外键索引
  KEY `fk_schedule_station` (`station_id`), -- 外键索引
  CONSTRAINT `fk_schedule_station` FOREIGN KEY (`station_id`) REFERENCES `Station` (`station_id`) ON DELETE CASCADE ON UPDATE CASCADE, -- 外键约束 (类型2)
  CONSTRAINT `fk_schedule_train` FOREIGN KEY (`train_id`) REFERENCES `Train` (`train_id`) ON DELETE CASCADE ON UPDATE CASCADE -- 外键约束 (类型2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='列车时刻表';

-- --------------------------------------------------
-- 插入示例数据
-- --------------------------------------------------

-- 插入线路数据
INSERT INTO `Line` (`line_name`, `status`, `open_date`) VALUES
('1号线', '运营', '2010-05-01'),
('2号线', '运营', '2012-10-01'),
('亦庄线', '运营', '2010-12-30'),
('S1线', '停运', '2017-12-30'),
('机场线', '运营', '2008-07-19');

-- 插入站点数据 (假设 Line ID 1, 2, 3 分别对应上面插入的 1号线, 2号线, 亦庄线)
INSERT INTO `Station` (`station_name`, `line_id`, `location_desc`, `is_transfer`) VALUES
('苹果园', 1, '石景山区苹果园交通枢纽', 0),
('古城', 1, '石景山区古城大街', 0),
('八角游乐园', 1, '石景山区石景山路', 0),
('西单', 1, '西城区西单北大街', 1), -- 换乘站
('王府井', 1, '东城区王府井大街', 0),
('复兴门', 2, '西城区复兴门内大街', 1), -- 换乘站
('车公庄', 2, '西城区车公庄大街', 0),
('西直门', 2, '西城区西直门外大街', 1), -- 换乘站
('积水潭', 2, '西城区新街口外大街', 0),
('东直门', 2, '东城区东直门外斜街', 1), -- 换乘站 (也连接机场线)
('宋家庄', 3, '丰台区宋家庄交通枢纽', 1), -- 换乘站
('肖村', 3, '丰台区成寿寺路', 0),
('小红门', 3, '朝阳区小红门路', 0),
('旧宫', 3, '大兴区旧宫镇', 0),
('亦庄桥', 3, '大兴区亦庄经济技术开发区', 0);


-- 插入列车数据
INSERT INTO `Train` (`train_number`, `line_id`, `model`, `capacity`, `status`) VALUES
('G101', 1, 'SFM04', 1480, '运行中'),
('G102', 1, 'SFM04', 1480, '运行中'),
('G201', 2, 'DKZ4', 1860, '运行中'),
('G202', 2, 'DKZ4', 1860, '维修中'),
('YIZ01', 3, 'SFM13', 1460, '运行中'),
('YIZ02', 3, 'SFM13', 1460, '运行中'),
('S101', 4, '磁悬浮', 1000, '运行中'); -- 属于已停运线路，但列车本身可能还在

-- 插入乘客数据
INSERT INTO `Passenger` (`name`, `phone_number`) VALUES
('张三', '13800138000'),
('李四', '13900139001'),
('王五', '13700137002'),
('赵六', '15800158003'),
('孙七', '15900159004');

-- 插入票务数据 (假设乘客ID 1, 2, 3 和 站点ID 4(西单), 5(王府井), 6(复兴门), 10(东直门) 存在)
INSERT INTO `Ticket` (`passenger_id`, `departure_station_id`, `arrival_station_id`, `price`, `payment_status`) VALUES
(1, 4, 5, 3.00, '已支付'), -- 张三: 西单 -> 王府井
(2, 6, 10, 4.00, '已支付'), -- 李四: 复兴门 -> 东直门
(1, 10, 6, 4.00, '已支付'), -- 张三: 东直门 -> 复兴门
(3, 1, 4, 5.00, '已支付'), -- 王五: 苹果园 -> 西单
(4, 11, 15, 3.00, '已支付'), -- 赵六: 宋家庄 -> 亦庄桥
(5, 15, 11, 3.00, '未支付'); -- 孙七: 亦庄桥 -> 宋家庄 (未支付)


-- 插入时刻表数据 (假设列车ID 1(G101), 3(G201), 5(YIZ01) 和 站点ID 1(苹果园), 2(古城), 6(复兴门), 7(车公庄), 11(宋家庄), 12(肖村) 存在)
INSERT INTO `Schedule` (`train_id`, `station_id`, `arrival_time`, `departure_time`, `schedule_date`) VALUES
(1, 1, NULL, '06:00:00', CURDATE()), -- G101 苹果园始发
(1, 2, '06:03:00', '06:04:00', CURDATE()), -- G101 到达古城
(1, 3, '06:07:00', '06:08:00', CURDATE()), -- G101 到达八角
(3, 6, NULL, '06:10:00', CURDATE()), -- G201 复兴门始发 (假设)
(3, 7, '06:14:00', '06:15:00', CURDATE()), -- G201 到达车公庄
(5, 11, NULL, '06:20:00', CURDATE()), -- YIZ01 宋家庄始发
(5, 12, '06:23:00', '06:24:00', CURDATE()); -- YIZ01 到达肖村

-- --------------------------------------------------
-- 约束类型总结:
-- 1. 主键约束 (PRIMARY KEY): 每个表都有 (line_id, station_id, train_id, passenger_id, ticket_id, schedule_id)
-- 2. 外键约束 (FOREIGN KEY): Station.line_id, Train.line_id, Ticket.passenger_id, Ticket.departure_station_id, Ticket.arrival_station_id, Schedule.train_id, Schedule.station_id
-- 3. 唯一约束 (UNIQUE KEY): Line.line_name, Station(station_name, line_id), Train.train_number, Passenger.phone_number, Schedule(train_id, station_id, schedule_date)
-- 4. 非空约束 (NOT NULL): Line.line_name, Station.station_name, Station.line_id, Train.train_number, Train.line_id, Passenger.name, Ticket.passenger_id, Ticket.departure_station_id, Ticket.arrival_station_id, Ticket.price, Schedule.train_id, Schedule.station_id, Schedule.schedule_date
-- 5. CHECK 约束 (CHECK): Ticket.price > 0
-- 6. 枚举约束 (ENUM): Line.status, Train.status, Ticket.payment_status
-- 7. 默认值约束 (DEFAULT): Line.status, Station.is_transfer, Train.status, Passenger.registration_date, Ticket.purchase_time, Ticket.payment_status
-- --------------------------------------------------
```

## 数据库查询示例
```sql
-- 使用数据库
USE `subway_system`;

-- 查询 1: 查询指定线路的所有站点信息 (单表查询)
-- 意图: 获取 '1号线' 的所有站点名称和位置描述。
-- 提取方式: 从 Station 表中筛选出 line_id 对应 '1号线' 的记录。
SELECT
    s.station_name AS '站点名称',
    s.location_desc AS '位置描述',
    s.is_transfer AS '是否换乘站'
FROM
    Station s
JOIN
    Line l ON s.line_id = l.line_id
WHERE
    l.line_name = '1号线'
ORDER BY
    s.station_id; -- 通常按站点顺序排序，这里用 ID 近似


-- 查询 2: 查询特定列车今天的运行时刻表 (连接查询)
-- 意图: 获取列车 'G101' 在今天 (CURDATE()) 经过的所有站点及其预计到发时间。
-- 提取方式: 连接 Schedule, Train, Station 表，筛选出指定 train_number 和 schedule_date 的记录。
SELECT
    t.train_number AS '列车编号',
    s.station_name AS '站点名称',
    sch.arrival_time AS '到达时间',
    sch.departure_time AS '出发时间'
FROM
    Schedule sch
JOIN
    Train t ON sch.train_id = t.train_id
JOIN
    Station s ON sch.station_id = s.station_id
WHERE
    t.train_number = 'G101' AND sch.schedule_date = CURDATE()
ORDER BY
    sch.departure_time, sch.arrival_time; -- 按时间顺序排序


-- 查询 3: 查询在 '西单' 站可以换乘哪些线路 (嵌套查询/子查询)
-- 意图: 找出除了 '西单' 站本身所属线路外，还有哪些线路也经过名为 '西单' 的站点（表示可换乘）。
-- 提取方式: 先找到名为 '西单' 的所有站点记录，获取它们的 line_id，然后查询这些 line_id 对应的线路名称。
SELECT
    l.line_name AS '可换乘线路'
FROM
    Line l
WHERE
    l.line_id IN (
        SELECT DISTINCT s.line_id
        FROM Station s
        WHERE s.station_name = '西单'
    );
-- 注意: 这个查询假设站名在不同线路中可能相同，用于查找所有包含此站名的线路。
-- 如果要查找标记为换乘站的线路，可以这样：
SELECT l.line_name FROM Line l JOIN Station s ON l.line_id = s.line_id WHERE s.station_name = '西单' AND s.is_transfer = 1;


-- 查询 4: 查询购买过两次及以上票的乘客信息 (分组和聚合查询)
-- 意图: 找出哪些乘客是常客（购票次数 >= 2）。
-- 提取方式: 按 passenger_id 对 Ticket 表进行分组，统计每个乘客的购票数量 (COUNT)，筛选出数量大于等于2的乘客ID，最后连接 Passenger 表获取乘客姓名和电话。
SELECT
    p.name AS '乘客姓名',
    p.phone_number AS '手机号',
    COUNT(t.ticket_id) AS '购票次数'
FROM
    Ticket t
JOIN
    Passenger p ON t.passenger_id = p.passenger_id
GROUP BY
    t.passenger_id, p.name, p.phone_number -- Group by all non-aggregated columns selected
HAVING
    COUNT(t.ticket_id) >= 2
ORDER BY
    `购票次数` DESC;


-- 查询 5: 查询从 '宋家庄' 出发，且票价高于平均票价的票务信息 (子查询/聚合函数)
-- 意图: 查找从特定站点出发的高价票记录。
-- 提取方式: 先计算出所有票的平均价格 (AVG(price))。然后在 Ticket 表中筛选出出发站点是 '宋家庄' 且价格高于该平均值的记录，并连接 Station 和 Passenger 表获取详细信息。
SELECT
    p.name AS '乘客姓名',
    dep_s.station_name AS '出发站',
    arr_s.station_name AS '到达站',
    t.price AS '票价',
    t.purchase_time AS '购买时间'
FROM
    Ticket t
JOIN
    Passenger p ON t.passenger_id = p.passenger_id
JOIN
    Station dep_s ON t.departure_station_id = dep_s.station_id
JOIN
    Station arr_s ON t.arrival_station_id = arr_s.station_id
WHERE
    dep_s.station_name = '宋家庄'
    AND t.price > (SELECT AVG(price) FROM Ticket);
```

## 视图、用户、角色和权限
```sql
-- 确保首先选择了正确的数据库
-- 建议在 Navicat 中先手动执行 USE subway_system; 确保上下文正确
USE `subway_system`;

-- --------------------------------------------------
-- 创建视图 1: 显示各线路的站点数量
-- 意图: 快速查看每条地铁线路包含多少个站点。
-- --------------------------------------------------
CREATE OR REPLACE VIEW `view_line_station_count` AS
SELECT
    l.line_name AS '线路名称',
    l.status AS '运营状态',
    COUNT(s.station_id) AS '站点数量'
FROM
    Line l
LEFT JOIN -- 使用 LEFT JOIN 保证即使线路没有站点也显示
    Station s ON l.line_id = s.line_id
GROUP BY
    l.line_id, l.line_name, l.status;

-- 查询视图 1 (可以在脚本执行后手动查询验证)
-- SELECT * FROM `view_line_station_count`;


-- --------------------------------------------------
-- 创建视图 2: 显示今天指定站点的列车到发信息 (简化版)
-- 意图: 方便乘客快速查询某个站点今天的列车时刻。以 '西单' 站为例。
-- --------------------------------------------------
CREATE OR REPLACE VIEW `view_station_schedule_today_xidan` AS
SELECT
    t.train_number AS '列车号',
    l.line_name AS '所属线路',
    s.station_name AS '当前站点',
    sch.arrival_time AS '预计到达',
    sch.departure_time AS '预计出发'
FROM
    Schedule sch
JOIN
    Train t ON sch.train_id = t.train_id
JOIN
    Station s ON sch.station_id = s.station_id
JOIN
    Line l ON s.line_id = l.line_id -- Assuming Station links directly to Line for simplicity here
WHERE
    sch.schedule_date = CURDATE()
    AND s.station_name = '西单' -- 特定站点
ORDER BY
    sch.arrival_time, sch.departure_time;

-- 查询视图 2 (可以在脚本执行后手动查询验证)
-- SELECT * FROM `view_station_schedule_today_xidan`;


-- --------------------------------------------------
-- 创建角色
-- 意图: 定义不同类型的用户权限集合。
-- --------------------------------------------------
CREATE ROLE IF NOT EXISTS 'passenger_role', 'admin_role';

-- --------------------------------------------------
-- 分配权限给角色
-- --------------------------------------------------
-- 乘客角色: 只能查询信息 (SELECT 权限)，可以查看线路、站点、时刻表、自己的票务信息
GRANT SELECT ON `subway_system`.`Line` TO 'passenger_role';
GRANT SELECT ON `subway_system`.`Station` TO 'passenger_role';
GRANT SELECT ON `subway_system`.`Train` TO 'passenger_role'; -- 允许查看列车基本信息
GRANT SELECT ON `subway_system`.`Schedule` TO 'passenger_role';
GRANT SELECT ON `subway_system`.`Ticket` TO 'passenger_role'; -- 乘客应只能查自己的票，这需要在应用层面控制，数据库层面授予表查询权限
GRANT SELECT ON `subway_system`.`Passenger` TO 'passenger_role'; -- 允许查看自己的信息
GRANT SELECT ON `subway_system`.`view_line_station_count` TO 'passenger_role';
GRANT SELECT ON `subway_system`.`view_station_schedule_today_xidan` TO 'passenger_role'; -- 允许查询视图
GRANT SELECT ON `subway_system`.`PointsOfInterest` TO 'passenger_role'; -- 允许乘客查询POI

-- 管理员角色: 拥有数据库的几乎所有权限
GRANT ALL PRIVILEGES ON `subway_system`.* TO 'admin_role'; -- 授予所有权限
GRANT GRANT OPTION ON `subway_system`.* TO 'admin_role'; -- 允许管理员授权给其他用户

-- --------------------------------------------------
-- 创建用户并分配角色
-- 意图: 创建具体的用户账号，并赋予预定义的角色。
-- --------------------------------------------------
-- 注意：如果用户已存在，CREATE USER IF NOT EXISTS 不会报错，也不会修改密码
CREATE USER IF NOT EXISTS 'passenger_user'@'localhost' IDENTIFIED BY 'password123';
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'adminpass456';

-- --------------------------------------------------
-- 为用户分配角色
-- --------------------------------------------------
GRANT 'passenger_role' TO 'passenger_user'@'localhost';
GRANT 'admin_role' TO 'admin_user'@'localhost';

-- --------------------------------------------------
-- 设置默认角色 (可选, 使角色在登录时自动激活)
-- 注意: 以下语法仅在 MySQL 8.0 及以上版本有效。如果您的版本较低，请注释掉这两行。
-- SET DEFAULT ROLE 'passenger_role' FOR 'passenger_user'@'localhost';
-- SET DEFAULT ROLE 'admin_role' FOR 'admin_user'@'localhost';
-- --------------------------------------------------

-- --------------------------------------------------
-- 刷新权限使更改生效
-- --------------------------------------------------
FLUSH PRIVILEGES;

-- --------------------------------------------------
-- 查看用户权限 (验证, 可在脚本执行后手动执行)
-- --------------------------------------------------
-- SHOW GRANTS FOR 'passenger_user'@'localhost';
-- SHOW GRANTS FOR 'admin_user'@'localhost';
-- 如果 MySQL 版本支持，可以使用 USING 查看通过角色获得的权限
-- SHOW GRANTS FOR 'passenger_user'@'localhost' USING 'passenger_role';
-- SHOW GRANTS FOR 'admin_user'@'localhost' USING 'admin_role';

```

## 存储过程和触发器
```sql
-- 使用数据库
USE `subway_system`;

-- 存储过程: 购买车票
-- 意图: 模拟乘客购买车票的过程，传入乘客ID、出发站ID、到达站ID和票价，自动插入一条票务记录。
DELIMITER //

CREATE PROCEDURE `sp_purchase_ticket`(
    IN p_passenger_id INT,
    IN p_departure_station_id INT,
    IN p_arrival_station_id INT,
    IN p_price DECIMAL(10, 2),
    OUT p_ticket_id INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE passenger_exists INT DEFAULT 0;
    DECLARE departure_station_exists INT DEFAULT 0;
    DECLARE arrival_station_exists INT DEFAULT 0;

    -- 检查输入参数有效性
    IF p_price <= 0 THEN
        SET p_message = '错误: 票价必须大于 0。';
        SET p_ticket_id = NULL;
    ELSE
        -- 检查乘客是否存在
        SELECT COUNT(*) INTO passenger_exists FROM Passenger WHERE passenger_id = p_passenger_id;
        -- 检查出发站点是否存在
        SELECT COUNT(*) INTO departure_station_exists FROM Station WHERE station_id = p_departure_station_id;
        -- 检查到达站点是否存在
        SELECT COUNT(*) INTO arrival_station_exists FROM Station WHERE station_id = p_arrival_station_id;

        IF passenger_exists = 0 THEN
            SET p_message = '错误: 乘客不存在。';
            SET p_ticket_id = NULL;
        ELSEIF departure_station_exists = 0 THEN
            SET p_message = '错误: 出发站点不存在。';
            SET p_ticket_id = NULL;
        ELSEIF arrival_station_exists = 0 THEN
            SET p_message = '错误: 到达站点不存在。';
            SET p_ticket_id = NULL;
        ELSE
            -- 插入票务记录
            INSERT INTO Ticket (passenger_id, departure_station_id, arrival_station_id, price, payment_status)
            VALUES (p_passenger_id, p_departure_station_id, p_arrival_station_id, p_price, '已支付'); -- 假设直接支付成功

            -- 获取新插入票的ID
            SET p_ticket_id = LAST_INSERT_ID();
            SET p_message = '购票成功！';
        END IF;
    END IF;
END //

DELIMITER ;

-- 调用存储过程示例 (假设乘客ID 1, 站点ID 4, 5 存在)
SET @ticket_id = 0;
SET @message = '';
CALL sp_purchase_ticket(1, 4, 5, 3.50, @ticket_id, @message);
SELECT @ticket_id, @message; -- 查看输出结果


-- 触发器: 记录列车状态变更日志
-- 意图: 当 Train 表的 status 字段发生变化时，自动在另一个日志表 (需要先创建) 中记录变更信息。
-- 首先，创建日志表
CREATE TABLE IF NOT EXISTS `TrainStatusLog` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `train_id` int NOT NULL,
  `old_status` enum('运行中','维修中') DEFAULT NULL,
  `new_status` enum('运行中','维修中') DEFAULT NULL,
  `change_time` timestamp DEFAULT CURRENT_TIMESTAMP,
  `changed_by` varchar(100) DEFAULT NULL, -- 记录修改者，通常是当前用户
  PRIMARY KEY (`log_id`),
  KEY `idx_train_id` (`train_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='列车状态变更日志';

-- 创建触发器
DELIMITER //

CREATE TRIGGER `trg_after_train_status_update`
AFTER UPDATE ON `Train`
FOR EACH ROW
BEGIN
    -- 仅当 status 字段实际发生变化时记录日志
    IF OLD.status <> NEW.status THEN
        INSERT INTO TrainStatusLog (train_id, old_status, new_status, changed_by)
        VALUES (OLD.train_id, OLD.status, NEW.status, CURRENT_USER()); -- CURRENT_USER() 获取当前执行操作的MySQL用户
    END IF;
END //

DELIMITER ;

-- 测试触发器 (假设列车ID 4 'G202' 存在且状态为 '维修中')
-- 查看当前状态
SELECT train_id, train_number, status FROM Train WHERE train_id = 4;
-- 更新状态
UPDATE Train SET status = '运行中' WHERE train_id = 4;
-- 再次查看状态
SELECT train_id, train_number, status FROM Train WHERE train_id = 4;
-- 查看日志表是否记录了变更
SELECT * FROM TrainStatusLog WHERE train_id = 4;

-- 再次更新状态，测试是否还记录
UPDATE Train SET status = '维修中' WHERE train_id = 4;
SELECT * FROM TrainStatusLog WHERE train_id = 4;

```