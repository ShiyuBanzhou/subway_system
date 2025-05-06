
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for farezone
-- ----------------------------
DROP TABLE IF EXISTS `farezone`;
CREATE TABLE `farezone`  (
  `zone_id` int NOT NULL AUTO_INCREMENT COMMENT '分区ID',
  `zone_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分区名称',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '描述（覆盖范围、特殊提示）',
  PRIMARY KEY (`zone_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '车费分区表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of farezone
-- ----------------------------
INSERT INTO `farezone` VALUES (1, '1区', '市中心及周边核心区域');
INSERT INTO `farezone` VALUES (2, '2区', '次核心区域');
INSERT INTO `farezone` VALUES (3, '3区', '远郊及延伸区域');

-- ----------------------------
-- Table structure for line
-- ----------------------------
DROP TABLE IF EXISTS `line`;
CREATE TABLE `line`  (
  `line_id` int NOT NULL AUTO_INCREMENT COMMENT '线路ID',
  `line_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '线路名称',
  `start_station_id` int NULL DEFAULT NULL COMMENT '首发站ID (逻辑关联)',
  `end_station_id` int NULL DEFAULT NULL COMMENT '终点站ID (逻辑关联)',
  `status` enum('运营','停运') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '运营' COMMENT '状态',
  `open_date` date NULL DEFAULT NULL COMMENT '开通日期',
  PRIMARY KEY (`line_id`) USING BTREE,
  UNIQUE INDEX `uq_line_name`(`line_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '地铁线路信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of line
-- ----------------------------
INSERT INTO `line` VALUES (1, '1号线', 1, 5, '运营', '2010-05-01');
INSERT INTO `line` VALUES (2, '2号线', 6, 10, '运营', '2012-10-01');
INSERT INTO `line` VALUES (3, '亦庄线', 11, 13, '运营', '2010-12-30');
INSERT INTO `line` VALUES (4, 'S1线', 16, 20, '停运', '2017-12-30');
INSERT INTO `line` VALUES (5, '机场线', 21, 24, '运营', '2008-07-19');
INSERT INTO `line` VALUES (6, '4号线', 26, 29, '运营', '2009-09-28');


-- ----------------------------
-- Table structure for maintenancerecord
-- ----------------------------
DROP TABLE IF EXISTS `maintenancerecord`;
CREATE TABLE `maintenancerecord`  (
  `record_id` int NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `equipment` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称（闸机/自动售票机等）',
  `station_id` int NOT NULL COMMENT '站点ID',
  `staff_id` int NULL DEFAULT NULL COMMENT '维修员工ID（可为空，用于 ON DELETE SET NULL）',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '问题描述及处理结果',
  PRIMARY KEY (`record_id`) USING BTREE,
  INDEX `station_id`(`station_id` ASC) USING BTREE,
  INDEX `staff_id`(`staff_id` ASC) USING BTREE,
  CONSTRAINT `fk_maint_staff` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_maint_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '站点设备维护记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of maintenancerecord
-- ----------------------------
INSERT INTO `maintenancerecord` VALUES (1, '闸机A1', 4, 3, '2025-04-28 10:00:00', '2025-04-28 12:00:00', '更换感应模块');
INSERT INTO `maintenancerecord` VALUES (2, '售票机B2', 8, 3, '2025-04-28 13:30:00', NULL, '系统升级中');

-- ----------------------------
-- Table structure for passenger
-- ----------------------------
DROP TABLE IF EXISTS `passenger`;
CREATE TABLE `passenger`  (
  `passenger_id` int NOT NULL AUTO_INCREMENT COMMENT '乘客ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '姓名',
  `phone_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '手机号',
  `registration_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册日期',
  PRIMARY KEY (`passenger_id`) USING BTREE,
  UNIQUE INDEX `uq_phone_number`(`phone_number` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '乘客信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of passenger
-- ----------------------------
INSERT INTO `passenger` VALUES (1, '张三', '13800138000', '2025-04-29 14:28:48');
INSERT INTO `passenger` VALUES (2, '李四', '13900139001', '2025-04-29 14:28:48');
INSERT INTO `passenger` VALUES (3, '王五', '13700137002', '2025-04-29 14:28:48');
INSERT INTO `passenger` VALUES (4, '赵六', '15800158003', '2025-04-29 14:28:48');
INSERT INTO `passenger` VALUES (5, '孙七', '15900159004', '2025-04-29 14:28:48');
INSERT INTO `passenger` VALUES (6, '周八', '13600136005', '2025-04-29 15:00:00');
INSERT INTO `passenger` VALUES (7, '吴九', '13700137006', '2025-04-29 15:05:00');
INSERT INTO `passenger` VALUES (8, '郑十', '13800138007', '2025-04-29 15:10:00');

-- ----------------------------
-- Table structure for pointsofinterest
-- ----------------------------
DROP TABLE IF EXISTS `pointsofinterest`;
CREATE TABLE `pointsofinterest`  (
  `poi_id` int NOT NULL AUTO_INCREMENT COMMENT '兴趣点ID',
  `station_id` int NOT NULL COMMENT '关联的站点ID',
  `poi_name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '兴趣点名称',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '分类 (如购物, 餐饮, 景点, 医疗等)',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '描述信息',
  PRIMARY KEY (`poi_id`) USING BTREE,
  INDEX `idx_station_id`(`station_id` ASC) USING BTREE,
  CONSTRAINT `fk_poi_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 19 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '站点周边兴趣点信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of pointsofinterest
-- ----------------------------
INSERT INTO `pointsofinterest` VALUES (1, 4, '西单大悦城', '购物', '大型综合购物中心，品牌众多');
INSERT INTO `pointsofinterest` VALUES (2, 4, '老佛爷百货(西单店)', '购物', '法国高端连锁百货');
INSERT INTO `pointsofinterest` VALUES (3, 4, '汉光百货', '购物', '北京老牌百货公司');
INSERT INTO `pointsofinterest` VALUES (4, 4, '西单图书大厦', '文化/购物', '大型图书销售中心');
INSERT INTO `pointsofinterest` VALUES (5, 6, '金融街购物中心', '购物', '服务金融区的高端购物场所');
INSERT INTO `pointsofinterest` VALUES (6, 6, '百盛购物中心(复兴门店)', '购物', '知名连锁百货');
INSERT INTO `pointsofinterest` VALUES (7, 8, '凯德MALL(西直门店)', '购物/餐饮', '集购物、餐饮、娱乐于一体');
INSERT INTO `pointsofinterest` VALUES (8, 8, '北京展览馆', '文化/会展', '经常举办大型展览和活动');
INSERT INTO `pointsofinterest` VALUES (9, 8, '北京动物园', '景点', '著名的城市动物园，适合亲子');
INSERT INTO `pointsofinterest` VALUES (10, 10, '来福士中心(东直门店)', '购物/餐饮', '现代化的购物中心');
INSERT INTO `pointsofinterest` VALUES (11, 10, '东方银座', '购物/办公', '综合性商业楼宇');
INSERT INTO `pointsofinterest` VALUES (12, 10, '簋街', '餐饮', '著名的餐饮一条街，以麻辣小龙虾闻名');
INSERT INTO `pointsofinterest` VALUES (13, 11, '首开福茂', '购物', '服务周边社区的购物中心');
INSERT INTO `pointsofinterest` VALUES (14, 1, '苹果园交通枢纽商业配套', '交通/商业', '地铁、公交枢纽站旁的商业设施');
INSERT INTO `pointsofinterest` VALUES (15, 16, '金安桥湿地公园', '景点', '湿地生态保护区，适合休闲漫步');
INSERT INTO `pointsofinterest` VALUES (16, 22, '三元桥购物中心', '购物', '大型综合购物中心');
INSERT INTO `pointsofinterest` VALUES (17, 25, '昌平区政府', '行政', '昌平区政府机构所在地');
INSERT INTO `pointsofinterest` VALUES (18, 20, '北京科技大学南校区', '教育', '北京科技大学南校区所在地');

-- ----------------------------
-- Table structure for routesegment
-- ----------------------------
DROP TABLE IF EXISTS `routesegment`;
CREATE TABLE `routesegment`  (
  `segment_id` int NOT NULL AUTO_INCREMENT COMMENT '路段ID',
  `line_id` int NOT NULL COMMENT '线路ID',
  `from_station` int NOT NULL COMMENT '起点站ID',
  `to_station` int NOT NULL COMMENT '终点站ID',
  `distance_km` decimal(5, 2) NOT NULL COMMENT '距离（公里）',
  PRIMARY KEY (`segment_id`) USING BTREE,
  INDEX `fk_seg_line`(`line_id` ASC) USING BTREE,
  INDEX `fk_seg_from_sta`(`from_station` ASC) USING BTREE,
  INDEX `fk_seg_to_sta`(`to_station` ASC) USING BTREE,
  CONSTRAINT `fk_seg_from_sta` FOREIGN KEY (`from_station`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_seg_line` FOREIGN KEY (`line_id`) REFERENCES `line` (`line_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_seg_to_sta` FOREIGN KEY (`to_station`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '线路相邻站点路段表，用于换乘及路径计算' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of routesegment
-- ----------------------------
INSERT INTO `routesegment` VALUES (1, 1, 1, 2, 2.50);
INSERT INTO `routesegment` VALUES (2, 1, 2, 3, 1.80);
INSERT INTO `routesegment` VALUES (3, 2, 6, 7, 2.20);
INSERT INTO `routesegment` VALUES (4, 3, 11, 12, 3.00);
INSERT INTO `routesegment` VALUES (5, 5, 10, 19, 4.50);

-- ----------------------------
-- Table structure for schedule
-- ----------------------------
DROP TABLE IF EXISTS `schedule`;
CREATE TABLE `schedule`  (
  `schedule_id` int NOT NULL AUTO_INCREMENT COMMENT '时刻表ID',
  `train_id` int NOT NULL COMMENT '列车ID',
  `station_id` int NOT NULL COMMENT '站点ID',
  `arrival_time` time NULL DEFAULT NULL COMMENT '预计到达时间',
  `departure_time` time NULL DEFAULT NULL COMMENT '预计出发时间',
  `schedule_date` date NOT NULL COMMENT '日期',
  PRIMARY KEY (`schedule_id`) USING BTREE,
  UNIQUE INDEX `uq_train_station_date`(`train_id` ASC, `station_id` ASC, `schedule_date` ASC) USING BTREE,
  INDEX `fk_schedule_train`(`train_id` ASC) USING BTREE,
  INDEX `fk_schedule_station`(`station_id` ASC) USING BTREE,
  CONSTRAINT `fk_schedule_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_schedule_train` FOREIGN KEY (`train_id`) REFERENCES `train` (`train_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 27 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '列车时刻表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of schedule
-- ----------------------------
INSERT INTO `schedule` VALUES (1, 1, 1, NULL, '06:00:00', '2025-04-29');
INSERT INTO `schedule` VALUES (2, 1, 2, '06:03:00', '06:04:00', '2025-04-29');
INSERT INTO `schedule` VALUES (3, 1, 3, '06:07:00', '06:08:00', '2025-04-29');
INSERT INTO `schedule` VALUES (4, 3, 6, NULL, '06:10:00', '2025-04-29');
INSERT INTO `schedule` VALUES (5, 3, 7, '06:14:00', '06:15:00', '2025-04-29');
INSERT INTO `schedule` VALUES (6, 5, 11, NULL, '06:20:00', '2025-04-29');
INSERT INTO `schedule` VALUES (7, 5, 12, '06:23:00', '06:24:00', '2025-04-29');
INSERT INTO `schedule` VALUES (8, 1, 4, '06:15:00', '06:16:00', '2025-04-29');
INSERT INTO `schedule` VALUES (9, 2, 1, '06:02:00', '06:03:00', '2025-04-29');
INSERT INTO `schedule` VALUES (10, 2, 2, '06:06:00', '06:07:00', '2025-04-29');
INSERT INTO `schedule` VALUES (11, 2, 3, '06:10:00', '06:11:00', '2025-04-29');
INSERT INTO `schedule` VALUES (12, 2, 4, '06:15:00', '06:16:00', '2025-04-29');
INSERT INTO `schedule` VALUES (13, 2, 5, '06:20:00', '06:21:00', '2025-04-29');
INSERT INTO `schedule` VALUES (14, 4, 6, '06:05:00', '06:06:00', '2025-04-29');
INSERT INTO `schedule` VALUES (15, 4, 7, '06:09:00', '06:10:00', '2025-04-29');
INSERT INTO `schedule` VALUES (16, 4, 8, '06:13:00', '06:14:00', '2025-04-29');
INSERT INTO `schedule` VALUES (17, 4, 9, '06:17:00', '06:18:00', '2025-04-29');
INSERT INTO `schedule` VALUES (18, 4, 10, '06:21:00', '06:22:00', '2025-04-29');
INSERT INTO `schedule` VALUES (19, 6, 11, '06:08:00', '06:09:00', '2025-04-29');
INSERT INTO `schedule` VALUES (20, 6, 12, '06:12:00', '06:13:00', '2025-04-29');
INSERT INTO `schedule` VALUES (21, 6, 13, '06:17:00', '06:18:00', '2025-04-29');
INSERT INTO `schedule` VALUES (22, 7, 14, '07:00:00', '07:01:00', '2025-04-29');
INSERT INTO `schedule` VALUES (23, 7, 15, '07:05:00', '07:06:00', '2025-04-29');
INSERT INTO `schedule` VALUES (24, 7, 16, '07:10:00', '07:11:00', '2025-04-29');
INSERT INTO `schedule` VALUES (25, 7, 17, '07:15:00', '07:16:00', '2025-04-29');
INSERT INTO `schedule` VALUES (26, 7, 18, '07:20:00', '07:21:00', '2025-04-29');

-- ----------------------------
-- Table structure for scheduleexception
-- ----------------------------
DROP TABLE IF EXISTS `scheduleexception`;
CREATE TABLE `scheduleexception`  (
  `exception_id` int NOT NULL AUTO_INCREMENT COMMENT '例外ID',
  `schedule_id` int NOT NULL COMMENT '时刻表ID',
  `reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '例外原因（维修/事故/特殊活动）',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '备注',
  PRIMARY KEY (`exception_id`) USING BTREE,
  INDEX `fk_exc_schedule`(`schedule_id` ASC) USING BTREE,
  CONSTRAINT `fk_exc_schedule` FOREIGN KEY (`schedule_id`) REFERENCES `schedule` (`schedule_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '时刻表变更或异常记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of scheduleexception
-- ----------------------------
INSERT INTO `scheduleexception` VALUES (1, 2, '维修', '车辆故障导致部分晚点');
INSERT INTO `scheduleexception` VALUES (2, 8, '活动', '重大活动延时发车');

-- ----------------------------
-- Table structure for servicealert
-- ----------------------------
DROP TABLE IF EXISTS `servicealert`;
CREATE TABLE `servicealert`  (
  `alert_id` int NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  `line_id` int NULL DEFAULT NULL COMMENT '影响线路ID（NULL:全网）',
  `station_id` int NULL DEFAULT NULL COMMENT '影响站点ID',
  `start_time` datetime NOT NULL COMMENT '生效时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `message` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告内容',
  PRIMARY KEY (`alert_id`) USING BTREE,
  INDEX `fk_alert_line`(`line_id` ASC) USING BTREE,
  INDEX `fk_alert_station`(`station_id` ASC) USING BTREE,
  CONSTRAINT `fk_alert_line` FOREIGN KEY (`line_id`) REFERENCES `line` (`line_id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_alert_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '临时服务中断或公告' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of servicealert
-- ----------------------------
INSERT INTO `servicealert` VALUES (1, 2, NULL, '2025-05-01 00:00:00', '2025-05-02 23:59:00', '2号线全线检修，部分车次停运');
INSERT INTO `servicealert` VALUES (2, NULL, 4, '2025-04-30 09:00:00', '2025-04-30 12:00:00', '西单站A口临时关闭，改由B口进出');

-- ----------------------------
-- Table structure for staff
-- ----------------------------
DROP TABLE IF EXISTS `staff`;
CREATE TABLE `staff`  (
  `staff_id` int NOT NULL AUTO_INCREMENT COMMENT '员工ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '姓名',
  `role` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '岗位（管理员/检票/维修/客服等）',
  `contact` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '联系方式',
  PRIMARY KEY (`staff_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '地铁系统运营员工' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of staff
-- ----------------------------
INSERT INTO `staff` VALUES (1, '张运营', '管理员', '010-12345678');
INSERT INTO `staff` VALUES (2, '李检票', '检票员', '010-23456789');
INSERT INTO `staff` VALUES (3, '王维保', '维修员', '010-34567890');

-- ----------------------------
-- Table structure for staffassignment
-- ----------------------------
DROP TABLE IF EXISTS `staffassignment`;
CREATE TABLE `staffassignment`  (
  `assign_id` int NOT NULL AUTO_INCREMENT COMMENT '排班ID',
  `staff_id` int NOT NULL COMMENT '员工ID',
  `station_id` int NOT NULL COMMENT '站点ID',
  `start_time` datetime NOT NULL COMMENT '班次开始',
  `end_time` datetime NOT NULL COMMENT '班次结束',
  PRIMARY KEY (`assign_id`) USING BTREE,
  INDEX `staff_id`(`staff_id` ASC) USING BTREE,
  INDEX `station_id`(`station_id` ASC) USING BTREE,
  CONSTRAINT `fk_assign_staff` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_assign_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '员工站点排班表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of staffassignment
-- ----------------------------
INSERT INTO `staffassignment` VALUES (1, 1, 4, '2025-04-29 06:00:00', '2025-04-29 14:00:00');
INSERT INTO `staffassignment` VALUES (2, 2, 8, '2025-04-29 06:00:00', '2025-04-29 14:00:00');
INSERT INTO `staffassignment` VALUES (3, 3, 14, '2025-04-29 08:00:00', '2025-04-29 16:00:00');

-- ----------------------------
-- Table structure for station
-- ----------------------------
DROP TABLE IF EXISTS `station`;
CREATE TABLE `station`  (
  `station_id` int NOT NULL AUTO_INCREMENT COMMENT '站点ID',
  `station_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '站点名称',
  `line_id` int NOT NULL COMMENT '所属线路ID',
  `location_desc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '站点位置描述',
  `is_transfer` tinyint(1) NULL DEFAULT 0 COMMENT '是否换乘站 (0:否, 1:是)',
  PRIMARY KEY (`station_id`) USING BTREE,
  UNIQUE INDEX `uq_station_name_line`(`station_name` ASC, `line_id` ASC) USING BTREE COMMENT '同一线路下站点名唯一',
  INDEX `fk_station_line`(`line_id` ASC) USING BTREE,
  CONSTRAINT `fk_station_line` FOREIGN KEY (`line_id`) REFERENCES `line` (`line_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 26 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '地铁站点信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of station
-- ----------------------------
INSERT INTO `station` VALUES (1, '苹果园', 1, '石景山区苹果园交通枢纽', 0);
INSERT INTO `station` VALUES (2, '古城', 1, '石景山区古城大街', 0);
INSERT INTO `station` VALUES (3, '八角游乐园', 1, '石景山区石景山路', 0);
INSERT INTO `station` VALUES (4, '西单', 1, '西城区西单北大街', 1);
INSERT INTO `station` VALUES (5, '王府井', 1, '东城区王府井大街', 0);
INSERT INTO `station` VALUES (6, '复兴门', 2, '西城区复兴门内大街', 1);
INSERT INTO `station` VALUES (7, '车公庄', 2, '西城区车公庄大街', 0);
INSERT INTO `station` VALUES (8, '西直门', 2, '西城区西直门外大街', 1);
INSERT INTO `station` VALUES (9, '积水潭', 2, '西城区新街口外大街', 0);
INSERT INTO `station` VALUES (10, '东直门', 2, '东城区东直门外斜街', 1);
INSERT INTO `station` VALUES (11, '宋家庄', 3, '丰台区宋家庄交通枢纽', 1);
INSERT INTO `station` VALUES (12, '肖村', 3, '丰台区成寿寺路', 0);
INSERT INTO `station` VALUES (13, '小红门', 3, '朝阳区小红门路', 0);
INSERT INTO `station` VALUES (14, '旧宫', 3, '大兴区旧宫镇', 0);
INSERT INTO `station` VALUES (15, '亦庄桥', 3, '大兴区亦庄经济技术开发区', 0);
INSERT INTO `station` VALUES (16, '金安桥', 4, '房山区金安桥镇', 0);
INSERT INTO `station` VALUES (17, '良乡大学城北', 4, '房山区良乡大学城北侧', 0);
INSERT INTO `station` VALUES (18, '良乡大学城', 4, '房山区良乡大学城', 0);
INSERT INTO `station` VALUES (19, '良乡大学城西', 4, '房山区良乡大学城西侧', 0);
INSERT INTO `station` VALUES (20, '良乡大学城南换乘', 4, '与燕房线换乘站点', 1);
INSERT INTO `station` VALUES (21, '东直门', 5, '东城区东直门外斜街', 1);
INSERT INTO `station` VALUES (22, '三元桥', 5, '朝阳区三元桥路', 0);
INSERT INTO `station` VALUES (23, '机场二号航站楼', 5, '顺义区空港街道', 0);
INSERT INTO `station` VALUES (24, '机场三号航站楼', 5, '顺义区', 0);
INSERT INTO `station` VALUES (25, '霍营', 5, '昌平区霍营镇', 1);
INSERT INTO `station` VALUES (26, '平安里', 6, '新街口南大街交汇平安里西大街', 1);
INSERT INTO `station` VALUES (27, '灵境胡同', 6, '西单附近', 0);
INSERT INTO `station` VALUES (28, '西单', 6, '西城区西单北大街', 1);
INSERT INTO `station` VALUES (29, '宣武门', 6, '宣武门外大街', 1);

-- ----------------------------
-- Table structure for ticket
-- ----------------------------
DROP TABLE IF EXISTS `ticket`;
CREATE TABLE `ticket`  (
  `ticket_id` int NOT NULL AUTO_INCREMENT COMMENT '票务ID',
  `passenger_id` int NOT NULL COMMENT '乘客ID',
  `purchase_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '购买时间',
  `departure_station_id` int NOT NULL COMMENT '出发站点ID',
  `arrival_station_id` int NOT NULL COMMENT '到达站点ID',
  `price` decimal(10, 2) NOT NULL COMMENT '票价',
  `payment_status` enum('已支付','未支付') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '已支付' COMMENT '支付状态',
  PRIMARY KEY (`ticket_id`) USING BTREE,
  INDEX `fk_ticket_passenger`(`passenger_id` ASC) USING BTREE,
  INDEX `fk_ticket_dep_station`(`departure_station_id` ASC) USING BTREE,
  INDEX `fk_ticket_arr_station`(`arrival_station_id` ASC) USING BTREE,
  CONSTRAINT `fk_ticket_arr_station` FOREIGN KEY (`arrival_station_id`) REFERENCES `station` (`station_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_ticket_dep_station` FOREIGN KEY (`departure_station_id`) REFERENCES `station` (`station_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_ticket_passenger` FOREIGN KEY (`passenger_id`) REFERENCES `passenger` (`passenger_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_price` CHECK (`price` > 0)
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '票务信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ticket
-- ----------------------------
INSERT INTO `ticket` VALUES (1, 1, '2025-04-29 14:28:48', 4, 5, 3.00, '已支付');
INSERT INTO `ticket` VALUES (2, 2, '2025-04-29 14:28:48', 6, 10, 4.00, '已支付');
INSERT INTO `ticket` VALUES (3, 1, '2025-04-29 14:28:48', 10, 6, 4.00, '已支付');
INSERT INTO `ticket` VALUES (4, 3, '2025-04-29 14:28:48', 1, 4, 5.00, '已支付');
INSERT INTO `ticket` VALUES (5, 4, '2025-04-29 14:28:48', 11, 15, 3.00, '已支付');
INSERT INTO `ticket` VALUES (6, 5, '2025-04-29 14:28:48', 15, 11, 3.00, '未支付');
INSERT INTO `ticket` VALUES (7, 1, '2025-04-29 14:48:06', 4, 5, 3.50, '已支付');
INSERT INTO `ticket` VALUES (8, 6, '2025-04-29 15:20:00', 4, 6, 5.50, '已支付');
INSERT INTO `ticket` VALUES (9, 7, '2025-04-29 15:25:00', 14, 18, 8.00, '未支付');

-- ----------------------------
-- Table structure for tickettype
-- ----------------------------
DROP TABLE IF EXISTS `tickettype`;
CREATE TABLE `tickettype`  (
  `type_id` int NOT NULL AUTO_INCREMENT COMMENT '票种ID',
  `type_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '票种名称（单程票/日票/月票等）',
  `base_price` decimal(8, 2) NOT NULL COMMENT '基础票价',
  `validity_minutes` int NOT NULL COMMENT '有效期（分钟）',
  PRIMARY KEY (`type_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '车票种类及价格规则' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of tickettype
-- ----------------------------
INSERT INTO `tickettype` VALUES (1, '单程票', 3.00, 90);
INSERT INTO `tickettype` VALUES (2, '日票', 18.00, 1440);
INSERT INTO `tickettype` VALUES (3, '月票', 160.00, 43200);

-- ----------------------------
-- Table structure for train
-- ----------------------------
DROP TABLE IF EXISTS `train`;
CREATE TABLE `train`  (
  `train_id` int NOT NULL AUTO_INCREMENT COMMENT '列车ID',
  `train_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '列车编号',
  `line_id` int NOT NULL COMMENT '所属线路ID',
  `model` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '列车型号',
  `capacity` int NULL DEFAULT NULL COMMENT '容量',
  `status` enum('运行中','维修中') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT '运行中' COMMENT '状态',
  PRIMARY KEY (`train_id`) USING BTREE,
  UNIQUE INDEX `uq_train_number`(`train_number` ASC) USING BTREE,
  INDEX `fk_train_line`(`line_id` ASC) USING BTREE,
  CONSTRAINT `fk_train_line` FOREIGN KEY (`line_id`) REFERENCES `line` (`line_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '地铁列车信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of train
-- ----------------------------
INSERT INTO `train` VALUES (1, 'G101', 1, 'SFM04', 1480, '运行中');
INSERT INTO `train` VALUES (2, 'G102', 1, 'SFM04', 1480, '运行中');
INSERT INTO `train` VALUES (3, 'G201', 2, 'DKZ4', 1860, '运行中');
INSERT INTO `train` VALUES (4, 'G202', 2, 'DKZ4', 1860, '维修中');
INSERT INTO `train` VALUES (5, 'YIZ01', 3, 'SFM13', 1460, '运行中');
INSERT INTO `train` VALUES (6, 'YIZ02', 3, 'SFM13', 1460, '运行中');
INSERT INTO `train` VALUES (7, 'S101', 4, '磁悬浮', 1000, '运行中');

-- ----------------------------
-- Table structure for trainstatuslog
-- ----------------------------
DROP TABLE IF EXISTS `trainstatuslog`;
CREATE TABLE `trainstatuslog`  (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `train_id` int NOT NULL,
  `old_status` enum('运行中','维修中') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `new_status` enum('运行中','维修中') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `change_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `changed_by` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  PRIMARY KEY (`log_id`) USING BTREE,
  INDEX `idx_train_id`(`train_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '列车状态变更日志' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of trainstatuslog
-- ----------------------------
INSERT INTO `trainstatuslog` VALUES (1, 4, '维修中', '运行中', '2025-04-29 14:48:06', 'root@localhost');
INSERT INTO `trainstatuslog` VALUES (2, 4, '运行中', '维修中', '2025-04-29 14:48:06', 'root@localhost');
INSERT INTO `trainstatuslog` VALUES (3, 4, '维修中', '运行中', '2025-04-29 15:33:37', 'root@localhost');
INSERT INTO `trainstatuslog` VALUES (4, 4, '运行中', '维修中', '2025-04-29 15:33:43', 'root@localhost');
INSERT INTO `trainstatuslog` VALUES (5, 5, '运行中', '维修中', '2025-04-28 10:00:00', 'system');
INSERT INTO `trainstatuslog` VALUES (6, 5, '维修中', '运行中', '2025-04-28 12:00:00', 'system');

-- ----------------------------
-- Table structure for turnstilelog
-- ----------------------------
DROP TABLE IF EXISTS `turnstilelog`;
CREATE TABLE `turnstilelog`  (
  `log_id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `passenger_id` int NOT NULL COMMENT '乘客ID',
  `station_id` int NOT NULL COMMENT '站点ID',
  `action` enum('IN','OUT') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '进/出',
  `timestamp` datetime NOT NULL COMMENT '操作时间',
  `ticket_id` int NULL DEFAULT NULL COMMENT '关联票务ID（可选）',
  PRIMARY KEY (`log_id`) USING BTREE,
  INDEX `passenger_id`(`passenger_id` ASC) USING BTREE,
  INDEX `station_id`(`station_id` ASC) USING BTREE,
  INDEX `fk_turnstile_ticket`(`ticket_id` ASC) USING BTREE,
  CONSTRAINT `fk_turnstile_passenger` FOREIGN KEY (`passenger_id`) REFERENCES `passenger` (`passenger_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_turnstile_station` FOREIGN KEY (`station_id`) REFERENCES `station` (`station_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_turnstile_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`ticket_id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '闸机刷票进出记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of turnstilelog
-- ----------------------------

-- ----------------------------
-- View structure for view_line_station_count
-- ----------------------------
DROP VIEW IF EXISTS `view_line_station_count`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `view_line_station_count` AS select `l`.`line_name` AS `线路名称`,`l`.`status` AS `运营状态`,count(`s`.`station_id`) AS `站点数量` from (`line` `l` left join `station` `s` on((`l`.`line_id` = `s`.`line_id`))) group by `l`.`line_id`,`l`.`line_name`,`l`.`status`;

-- ----------------------------
-- View structure for view_station_schedule_today_xidan
-- ----------------------------
DROP VIEW IF EXISTS `view_station_schedule_today_xidan`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `view_station_schedule_today_xidan` AS select `t`.`train_number` AS `列车号`,`l`.`line_name` AS `所属线路`,`s`.`station_name` AS `当前站点`,`sch`.`arrival_time` AS `预计到达`,`sch`.`departure_time` AS `预计出发` from (((`schedule` `sch` join `train` `t` on((`sch`.`train_id` = `t`.`train_id`))) join `station` `s` on((`sch`.`station_id` = `s`.`station_id`))) join `line` `l` on((`s`.`line_id` = `l`.`line_id`))) where ((`sch`.`schedule_date` = curdate()) and (`s`.`station_name` = '西单')) order by `sch`.`arrival_time`,`sch`.`departure_time`;

-- ----------------------------
-- Procedure structure for sp_purchase_ticket
-- ----------------------------
DROP PROCEDURE IF EXISTS `sp_purchase_ticket`;
delimiter ;;
CREATE PROCEDURE `sp_purchase_ticket`(IN p_passenger_id INT,
    IN p_departure_station_id INT,
    IN p_arrival_station_id INT,
    IN p_price DECIMAL(10, 2),
    OUT p_ticket_id INT,
    OUT p_message VARCHAR(255))
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
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table train
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_after_train_status_update`;
delimiter ;;
CREATE TRIGGER `trg_after_train_status_update` AFTER UPDATE ON `train` FOR EACH ROW BEGIN
    -- 仅当 status 字段实际发生变化时记录日志
    IF OLD.status <> NEW.status THEN
        INSERT INTO TrainStatusLog (train_id, old_status, new_status, changed_by)
        VALUES (OLD.train_id, OLD.status, NEW.status, CURRENT_USER()); -- CURRENT_USER() 获取当前执行操作的MySQL用户
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
