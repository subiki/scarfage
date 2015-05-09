-- phpMyAdmin SQL Dump
-- version 4.3.12
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: May 08, 2015 at 02:44 AM
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
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `images`
--

INSERT INTO `images` (`uid`, `filename`, `tag`) VALUES
(17, '3d6165cefaa3406a9e5a566fd1a38530.jpg', 'front'),
(20, '1335bf359cf942048b1085a607f05c5d.jpg', 'kmkk'),
(21, 'c3b9f22117ec4dec9ad0808bb50ddfc9.jpg', 'lklkjkekle'),
(22, 'fd5388a04cb64272ac564bd0dfb9f8f3.jpg', 'front'),
(23, '329813ed677f4964ae26dd3071371ea9.jpg', 'ecs'),
(24, 'bb844a8033684b5cbec62c1ff46b4163.jpeg', 'front'),
(25, '590dfaf739b44eb2864be625eaed2957.png', 'front'),
(26, '51e9b8091f794c5191fba242abbb785a.jpeg', 'wtf'),
(27, '46962606557440fc9eec0dc6b6778b77.jpg', 'front'),
(28, 'f8764b0383714e9fa01fe4470208dcd3.jpg', 'front'),
(29, 'cd07c133445d4392938ed219ab93bbe4.jpg', 'front'),
(30, '276f9f0c806041379ffc8a3817f91b8a.jpg', 'fix'),
(31, '76145b5cd4544132a72f8f105d875cb2.jpg', 'beer'),
(32, '78b2391e53fa41d9862d0510b4832eb0.png', 'front'),
(33, 'cf342b3ac5fe4bdf82531cd26c6cd68b.jpg', 'back'),
(34, '9895f6a672014a1884626a780709df58.jpg', 'front'),
(35, '34cf3add7db14216bcd6db45aa8cfaf0.jpg', 'front'),
(36, '56fba7bc3d544950a48124216aa3ca31.jpg', 'Little Bobby Tables;delete from ownwant;'),
(38, '22bfdc25c5c24a138f85de33ef7e951f.jpg', 'ascii THIS'),
(39, 'f33043abb2a74aa5b45be07e5f3c8959.JPG', 'wall'),
(40, '0719f7d1274b423e9122182096751e32.jpg', 'joe'),
(41, '1fde0d7377844cebb18d1b5ae3312854.jpg', 'tat'),
(42, 'a39bed59e9fe430984bb1fed7a93913f.png', 'fuck yea'),
(45, '54ce7f5d896543dfacb4e037637f35cb.jpg', 'nexus'),
(46, 'c88276c72b6043e381e16512203e38fb.jpg', 'tetris'),
(47, 'b4c34977e5934f45944903493de3822f.png', 'thats right');

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

--
-- Dumping data for table `imgmods`
--

INSERT INTO `imgmods` (`imgid`, `status`, `flag`, `username`) VALUES
(33, 0, 0, 'Zirra'),
(34, 0, 0, 'Zirra'),
(38, 0, 0, 'Zirra'),
(39, 0, 0, 'Zirra'),
(40, 0, 0, 'Zirra'),
(41, 0, 0, 'Zirra'),
(42, 0, 0, 'admin'),
(43, 0, 1, 'admin'),
(44, 0, 0, 'Zirra'),
(45, 0, 0, 'Zirra'),
(46, 0, 0, 'Zirra'),
(47, 0, 0, 'Zirra');

-- --------------------------------------------------------

--
-- Table structure for table `itemimg`
--

CREATE TABLE IF NOT EXISTS `itemimg` (
  `itemid` int(32) NOT NULL,
  `imgid` int(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `itemimg`
--

INSERT INTO `itemimg` (`itemid`, `imgid`) VALUES
(18, 17),
(17, 20),
(17, 21),
(20, 22),
(17, 23),
(21, 24),
(22, 25),
(21, 26),
(24, 27),
(25, 28),
(27, 29),
(24, 30),
(23, 31),
(29, 32),
(29, 33),
(30, 34),
(31, 35),
(32, 36),
(35, 38),
(37, 39),
(38, 40),
(39, 41),
(40, 42),
(43, 45),
(44, 46),
(45, 47);

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
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `items`
--

INSERT INTO `items` (`uid`, `name`, `description`, `added`, `modified`) VALUES
(17, 'ecs', 'Description', '2015-05-05', '2015-05-05'),
(18, 'test', 'Description', '2015-05-05', '2015-05-05'),
(20, 'fuck yea awesome scarf', 'Description', '2015-05-06', '2015-05-06'),
(21, 'wtf', 'Description', '2015-05-06', '2015-05-06'),
(22, 'triforce', 'Feel the power!', '2015-05-06', '2015-05-06'),
(23, 'beer', 'fuck yea, beer.', '2015-05-07', '2015-05-07'),
(24, 'testtt', 'Description', '2015-05-07', '2015-05-07'),
(25, 'bowtie', 'bow ties are cool.', '2015-05-07', '2015-05-07'),
(27, 'ecp', 'Description', '2015-05-07', '2015-05-07'),
(29, 'Zirra1', 'Test 1', '2015-05-07', '2015-05-07'),
(30, 'this', 'this 3', '2015-05-07', '2015-05-07'),
(31, 'fuck vancouver', 'wankouver whitecraps', '2015-05-07', '2015-05-07'),
(32, 'sql inject test', 'Description', '2015-05-07', '2015-05-07'),
(33, 'test6', 'Description', '2015-05-07', '2015-05-07'),
(34, 'exeuploadtest', 'Description', '2015-05-07', '2015-05-07'),
(35, 'exetest', 'Description', '2015-05-07', '2015-05-07'),
(36, 'ldldldld', 'Description', '2015-05-07', '2015-05-07'),
(37, 'more ascii fun', 'Description', '2015-05-07', '2015-05-07'),
(38, 'ascii', 'Description', '2015-05-07', '2015-05-07'),
(39, 'tat', 'Description', '2015-05-07', '2015-05-07'),
(40, 'stuff', 'Description', '2015-05-07', '2015-05-07'),
(43, 'this is how all phones should be', '', '2015-05-07', '2015-05-07'),
(44, 'tetris', 'Description', '2015-05-07', '2015-05-07'),
(45, 'the mother fucking greatest', 'the greatestDescription', '2015-05-07', '2015-05-07');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE IF NOT EXISTS `messages` (
  `uid` int(32) NOT NULL,
  `fromuserid` int(32) NOT NULL,
  `touserid` int(32) NOT NULL,
  `message` text NOT NULL,
  `status` int(8) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ownwant`
--

INSERT INTO `ownwant` (`uid`, `userid`, `itemid`, `own`, `willtrade`, `want`, `hidden`) VALUES
(9, 25, 18, 1, 0, 1, 0),
(10, 25, 17, 1, 1, 0, 0),
(11, 26, 17, 0, 0, 1, 0),
(13, 26, 18, 1, 1, 0, 0),
(15, 25, 20, 1, 1, 1, 0),
(17, 27, 20, 0, 0, 1, 0),
(18, 27, 18, 0, 0, 1, 0),
(19, 27, 22, 1, 0, 0, 0),
(20, 25, 22, 0, 0, 1, 0),
(21, 27, 27, 0, 0, 1, 0),
(23, 28, 31, 1, 0, 0, 0),
(24, 28, 25, 1, 1, 1, 0);

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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
  `lastseen` date DEFAULT NULL,
  `numadds` int(32) NOT NULL DEFAULT '0',
  `accesslevel` int(32) NOT NULL DEFAULT '0'
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`uid`, `username`, `pwhash`, `pwsalt`, `email`, `joined`, `lastseen`, `numadds`, `accesslevel`) VALUES
(25, 'admin', '3f24653f8fa7815ecb2a35f8960e352b49e74f14028b78070e1ce43e', '82AA87', 'email@am.com', '2015-04-11', '2015-05-08', 22, 255),
(26, 'testuser', 'd09ed5ae1c102a4b3d0608bf6d92f3297d37edf1c49411ddfdeeb8ca', 'E0197E', 'email@am.com', '2015-05-06', '2015-05-06', 1, 10),
(27, 'subiki', 'e996396c29ba1d32e3b79809371b117e116000d3a790c15b1bb5979a', 'AB3612', 'karmicj@gmail.com', '2015-05-06', '2015-05-08', 6, 255),
(28, 'Zirra', 'f576a73aba47eb268c7c4027b6b4565167159973eb4638cd71789439', '3B7AE6', 'thescottzirra@gmail.com', '2015-05-07', '2015-05-07', 12, 255);

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
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `images`
--
ALTER TABLE `images`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=48;
--
-- AUTO_INCREMENT for table `items`
--
ALTER TABLE `items`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=46;
--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `ownwant`
--
ALTER TABLE `ownwant`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=25;
--
-- AUTO_INCREMENT for table `tradelist`
--
ALTER TABLE `tradelist`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `uid` int(32) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=29;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
