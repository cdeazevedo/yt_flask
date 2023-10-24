DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);

DROP TABLE IF EXISTS channels
CREATE TABLE `channels` (
  `channel_id` varchar(255) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `thumbnail_uri` varchar(255) DEFAULT NULL,
  `published_date` datetime DEFAULT NULL,
  PRIMARY KEY (`channel_id`)
);
