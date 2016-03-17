-- MySQL dump 10.13  Distrib 5.5.47, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: scarfage
-- ------------------------------------------------------
-- Server version	5.5.47-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `images` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `tag` varchar(200) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `userid` int(11) DEFAULT NULL,
  `ip` int(32) NOT NULL,
  `image` longblob NOT NULL,
  `parent` int(32) NOT NULL,
  UNIQUE KEY `uid` (`uid`),
  KEY `userid` (`userid`),
  KEY `ip` (`ip`),
  KEY `fk_images_1_idx` (`parent`),
  CONSTRAINT `images_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `images_ibfk_2` FOREIGN KEY (`ip`) REFERENCES `ip` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `imgmods`
--

DROP TABLE IF EXISTS `imgmods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `imgmods` (
  `imgid` int(32) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `flag` tinyint(1) NOT NULL DEFAULT '0',
  `userid` int(11) DEFAULT NULL,
  UNIQUE KEY `imgid` (`imgid`),
  KEY `userid` (`userid`),
  CONSTRAINT `imgmods_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ip`
--

DROP TABLE IF EXISTS `ip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ip` (
  `uid` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`uid`),
  UNIQUE KEY `ip` (`ip`),
  KEY `uid` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `itemedits`
--

DROP TABLE IF EXISTS `itemedits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `itemedits` (
  `uid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `itemid` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `userid` int(11) DEFAULT NULL,
  `ip` int(11) NOT NULL,
  `body` varchar(20000) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  UNIQUE KEY `uid` (`uid`),
  KEY `itemid` (`itemid`),
  KEY `userid` (`userid`),
  KEY `ip` (`ip`),
  CONSTRAINT `itemedits_ibfk_1` FOREIGN KEY (`itemid`) REFERENCES `items` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `itemedits_ibfk_2` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `itemedits_ibfk_3` FOREIGN KEY (`itemid`) REFERENCES `items` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `itemedits_ibfk_4` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `itemedits_ibfk_5` FOREIGN KEY (`ip`) REFERENCES `ip` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `items` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` int(11) NOT NULL,
  `added` datetime NOT NULL,
  `modified` datetime NOT NULL,
  UNIQUE KEY `uid` (`uid`),
  KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=179 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `itemtags`
--

DROP TABLE IF EXISTS `itemtags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `itemtags` (
  `itemid` int(11) NOT NULL,
  `tag` varchar(255) NOT NULL,
  UNIQUE KEY `fk_itemtags_1_idx` (`itemid`,`tag`),
  CONSTRAINT `fk_itemtags_1` FOREIGN KEY (`itemid`) REFERENCES `items` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messages` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `fromuserid` int(32) NOT NULL,
  `touserid` int(32) NOT NULL,
  `subject` varchar(512) NOT NULL,
  `message` text NOT NULL,
  `status` int(8) NOT NULL,
  `parent` int(32) DEFAULT NULL,
  `sent` datetime NOT NULL,
  UNIQUE KEY `uid` (`uid`),
  KEY `parent` (`parent`),
  KEY `messages_ibfk_1` (`fromuserid`),
  KEY `messages_ibfk_2` (`touserid`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`fromuserid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`touserid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`parent`) REFERENCES `messages` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ownwant`
--

DROP TABLE IF EXISTS `ownwant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ownwant` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `userid` int(32) NOT NULL,
  `itemid` int(32) NOT NULL,
  `own` tinyint(1) NOT NULL DEFAULT '0',
  `willtrade` tinyint(1) NOT NULL DEFAULT '0',
  `want` tinyint(1) NOT NULL DEFAULT '0',
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  UNIQUE KEY `uid` (`uid`),
  KEY `ownwant_ibfk_2` (`itemid`),
  KEY `ownwant_ibfk_1` (`userid`),
  CONSTRAINT `ownwant_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `ownwant_ibfk_2` FOREIGN KEY (`itemid`) REFERENCES `items` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tradelist`
--

DROP TABLE IF EXISTS `tradelist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tradelist` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `itemid` int(32) NOT NULL,
  `messageid` int(32) NOT NULL,
  `userid` int(32) NOT NULL,
  `acceptstatus` tinyint(1) NOT NULL,
  UNIQUE KEY `uid` (`uid`),
  KEY `tradelist_ibfk_3` (`userid`),
  KEY `tradelist_ibfk_1` (`itemid`),
  KEY `tradelist_ibfk_2` (`messageid`),
  CONSTRAINT `tradelist_ibfk_1` FOREIGN KEY (`itemid`) REFERENCES `items` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `tradelist_ibfk_2` FOREIGN KEY (`messageid`) REFERENCES `messages` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `tradelist_ibfk_3` FOREIGN KEY (`userid`) REFERENCES `users` (`uid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tree`
--

DROP TABLE IF EXISTS `tree`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tree` (
  `ref` int(11) NOT NULL AUTO_INCREMENT,
  `parent` int(11) DEFAULT NULL,
  `lhs` int(11) DEFAULT NULL,
  `rhs` int(11) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ref`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=118 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `username` varchar(32) NOT NULL,
  `pwhash` varchar(200) NOT NULL,
  `email` varchar(200) NOT NULL,
  `joined` datetime DEFAULT NULL,
  `accesslevel` int(32) NOT NULL DEFAULT '0',
  UNIQUE KEY `uid` (`uid`),
  KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=332 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `userstat_lastseen`
--

DROP TABLE IF EXISTS `userstat_lastseen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userstat_lastseen` (
  `uid` int(11) NOT NULL,
  `date` datetime NOT NULL,
  UNIQUE KEY `uid` (`uid`),
  CONSTRAINT `userstat_lastseen_ibfk_1` FOREIGN KEY (`uid`) REFERENCES `users` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-03-16 21:46:58
