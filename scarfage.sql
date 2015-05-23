-- MySQL dump 10.13  Distrib 5.5.41, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: scarfage
-- ------------------------------------------------------
-- Server version	5.5.41-0+wheezy1

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
  `filename` varchar(200) NOT NULL,
  `tag` varchar(200) NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=115 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `images`
--

LOCK TABLES `images` WRITE;
/*!40000 ALTER TABLE `images` DISABLE KEYS */;
/*!40000 ALTER TABLE `images` ENABLE KEYS */;
UNLOCK TABLES;

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
  `username` varchar(200) NOT NULL,
  UNIQUE KEY `imgid` (`imgid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `imgmods`
--

LOCK TABLES `imgmods` WRITE;
/*!40000 ALTER TABLE `imgmods` DISABLE KEYS */;
/*!40000 ALTER TABLE `imgmods` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `itemimg`
--

DROP TABLE IF EXISTS `itemimg`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `itemimg` (
  `itemid` int(32) NOT NULL,
  `imgid` int(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `itemimg`
--

LOCK TABLES `itemimg` WRITE;
/*!40000 ALTER TABLE `itemimg` DISABLE KEYS */;
/*!40000 ALTER TABLE `itemimg` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `items` (
  `uid` int(32) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` text NOT NULL,
  `added` date NOT NULL,
  `modified` date NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

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
  `parent` int(11) NOT NULL,
  `sent` datetime NOT NULL,
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

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
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=127 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ownwant`
--

LOCK TABLES `ownwant` WRITE;
/*!40000 ALTER TABLE `ownwant` DISABLE KEYS */;
/*!40000 ALTER TABLE `ownwant` ENABLE KEYS */;
UNLOCK TABLES;

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
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tradelist`
--

LOCK TABLES `tradelist` WRITE;
/*!40000 ALTER TABLE `tradelist` DISABLE KEYS */;
/*!40000 ALTER TABLE `tradelist` ENABLE KEYS */;
UNLOCK TABLES;

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
  `pwsalt` varchar(20) NOT NULL,
  `email` varchar(200) NOT NULL,
  `joined` date DEFAULT NULL,
  `accesslevel` int(32) NOT NULL DEFAULT '0',
  PRIMARY KEY (`uid`),
  UNIQUE KEY `uid` (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (25,'admin','3f24653f8fa7815ecb2a35f8960e352b49e74f14028b78070e1ce43e','82AA87','email@am.com','2015-04-11',255),(26,'testuser','d09ed5ae1c102a4b3d0608bf6d92f3297d37edf1c49411ddfdeeb8ca','E0197E','email@am.com','2015-05-06',10),(27,'subiki','e996396c29ba1d32e3b79809371b117e116000d3a790c15b1bb5979a','AB3612','karmicj@gmail.com','2015-05-06',255),(28,'Zirra','f576a73aba47eb268c7c4027b6b4565167159973eb4638cd71789439','3B7AE6','thescottzirra@gmail.com','2015-05-07',255);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userstat_lastseen`
--

DROP TABLE IF EXISTS `userstat_lastseen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userstat_lastseen` (
  `uid` int(11) NOT NULL,
  `date` date NOT NULL,
  UNIQUE KEY `uid` (`uid`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userstat_lastseen`
--

LOCK TABLES `userstat_lastseen` WRITE;
/*!40000 ALTER TABLE `userstat_lastseen` DISABLE KEYS */;
INSERT INTO `userstat_lastseen` VALUES (25,'2015-05-23'),(26,'2015-05-22'),(27,'2015-04-11'),(28,'2015-04-11');
/*!40000 ALTER TABLE `userstat_lastseen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userstat_uploads`
--

DROP TABLE IF EXISTS `userstat_uploads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userstat_uploads` (
  `uid` int(11) NOT NULL,
  `itemid` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userstat_uploads`
--

LOCK TABLES `userstat_uploads` WRITE;
/*!40000 ALTER TABLE `userstat_uploads` DISABLE KEYS */;
/*!40000 ALTER TABLE `userstat_uploads` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-05-23  8:22:13
