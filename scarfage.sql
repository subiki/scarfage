-- phpMyAdmin SQL Dump
-- version 4.3.12
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 23, 2015 at 04:32 AM
-- Server version: 5.5.41-0+wheezy1-log
-- PHP Version: 5.4.39-0+deb7u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `scarfage`
--

-- --------------------------------------------------------

--
-- Table structure for table `images`
--

CREATE TABLE IF NOT EXISTS `images` (
  `uid` int(32) NOT NULL,
  `filename` varchar(200) NOT NULL,
  `tag` varchar(200) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `imgmods`
--

CREATE TABLE IF NOT EXISTS `imgmods` (
  `imgid` int(32) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `flag` tinyint(1) NOT NULL DEFAULT '0',
  `username` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `itemimg`
--

CREATE TABLE IF NOT EXISTS `itemimg` (
  `itemid` int(32) NOT NULL,
  `imgid` int(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `items`
--

CREATE TABLE IF NOT EXISTS `items` (
  `uid` int(32) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text NOT NULL,
  `added` date NOT NULL,
  `modified` date NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE IF NOT EXISTS `messages` (
  `uid` int(32) NOT NULL,
  `fromuserid` int(32) NOT NULL,
  `touserid` int(32) NOT NULL,
  `subject` varchar(512) NOT NULL,
  `message` text NOT NULL,
  `status` int(8) NOT NULL,
  `parent` int(11) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `ownwant`
--

CREATE TABLE IF NOT EXISTS `ownwant` (
  `uid` int(32) NOT NULL,
  `userid` int(32) NOT NULL,
  `itemid` int(32) NOT NULL,
  `own` tinyint(1) NOT NULL DEFAULT '0',
  `willtrade` tinyint(1) NOT NULL DEFAULT '0',
  `want` tinyint(1) NOT NULL DEFAULT '0',
  `hidden` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tradelist`
--

CREATE TABLE IF NOT EXISTS `tradelist` (
  `uid` int(32) NOT NULL,
  `itemid` int(32) NOT NULL,
  `messageid` int(32) NOT NULL,
  `userid` int(32) NOT NULL,
  `acceptstatus` tinyint(1) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
  `uid` int(32) NOT NULL,
  `username` varchar(32) NOT NULL,
  `pwhash` varchar(200) NOT NULL,
  `pwsalt` varchar(20) NOT NULL,
  `email` varchar(200) NOT NULL,
  `joined` date DEFAULT NULL,
  `accesslevel` int(32) NOT NULL DEFAULT '0'
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`uid`, `username`, `pwhash`, `pwsalt`, `email`, `joined`, `accesslevel`) VALUES
(25, 'admin', '3f24653f8fa7815ecb2a35f8960e352b49e74f14028b78070e1ce43e', '82AA87', 'chris@mazuc.net', '2015-04-20', 255),
(26, 'testuser', 'd09ed5ae1c102a4b3d0608bf6d92f3297d37edf1c49411ddfdeeb8ca', 'E0197E', 'email@am.com', '2015-05-06', 10),
(27, 'subiki', 'e996396c29ba1d32e3b79809371b117e116000d3a790c15b1bb5979a', 'AB3612', 'karmicj@gmail.com', '2015-04-20', 255),
(28, 'Zirra', 'f576a73aba47eb268c7c4027b6b4565167159973eb4638cd71789439', '3B7AE6', 'thescottzirra@gmail.com', '2015-04-20', 255),
(29, 'cherz', 'c417735404e2631283535e079b3cb80ac186e61077d1777f16f18afb', '924E20', 'cherz007@me.com', '2015-05-18', 1);

-- --------------------------------------------------------

--
-- Table structure for table `userstat_lastseen`
--

CREATE TABLE IF NOT EXISTS `userstat_lastseen` (
  `uid` int(11) NOT NULL,
  `date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `userstat_lastseen`
--

INSERT INTO `userstat_lastseen` (`uid`, `date`) VALUES
(25, '2015-05-23'),
(26, '2015-04-20'),
(27, '2015-04-20'),
(28, '2015-04-20'),
(29, '2015-04-20');

-- --------------------------------------------------------

--
-- Table structure for table `userstat_uploads`
--

CREATE TABLE IF NOT EXISTS `userstat_uploads` (
  `uid` int(11) NOT NULL,
  `itemid` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `userstat_uploads`
--

INSERT INTO `userstat_uploads` (`uid`, `itemid`) VALUES
(25, 55),
(25, 56);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `images`
--
ALTER TABLE `images`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `imgmods`
--
ALTER TABLE `imgmods`
  ADD PRIMARY KEY (`imgid`), ADD UNIQUE KEY `imgid` (`imgid`);

--
-- Indexes for table `items`
--
ALTER TABLE `items`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `ownwant`
--
ALTER TABLE `ownwant`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `tradelist`
--
ALTER TABLE `tradelist`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`uid`), ADD UNIQUE KEY `uid` (`uid`);

--
-- Indexes for table `userstat_lastseen`
--
ALTER TABLE `userstat_lastseen`
  ADD UNIQUE KEY `uid` (`uid`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `images`
--
ALTER TABLE `images`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=65;
--
-- AUTO_INCREMENT for table `items`
--
ALTER TABLE `items`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=57;
--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=11;
--
-- AUTO_INCREMENT for table `ownwant`
--
ALTER TABLE `ownwant`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=63;
--
-- AUTO_INCREMENT for table `tradelist`
--
ALTER TABLE `tradelist`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=14;
--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=30;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
