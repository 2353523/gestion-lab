-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Apr 15, 2025 at 12:09 PM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `gestion_lab`
--

-- --------------------------------------------------------

--
-- Table structure for table `article`
--

DROP TABLE IF EXISTS `article`;
CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `id_type` int NOT NULL,
  `ghs_codes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `article`
--

INSERT INTO `article` (`id_article`, `nom_article`, `unite_mesure`, `date_expiration`, `id_type`, `ghs_codes`) VALUES
(1, 'becher', 'litre', NULL, 1, NULL),
(2, 'meden', 'litre', NULL, 1, NULL),
(7, 'pipette 20mL', 'unité', '2025-04-17 00:00:00', 1, NULL),
(8, 'bêcher  50mL', 'unité', NULL, 4, NULL),
(9, 'pippet10ml', 'unité', NULL, 1, NULL),
(10, 'NaOH', 'litre', NULL, 3, '06'),
(11, 'NaOH', 'litre', NULL, 3, '06'),
(12, 'HCl 2mol/L', 'litre', NULL, 2, ''),
(13, 'clim 12', 'unité', NULL, 5, NULL),
(14, 'sidahmed', 'litre', '2025-04-18 00:00:00', 2, NULL),
(15, 'sidahmed', 'kg', '2025-04-11 00:00:00', 1, NULL),
(16, 'sidahmed', 'kg', '2025-04-11 00:00:00', 1, '01,02'),
(18, 'sidahmed43', 'unité', '2025-05-07 00:00:00', 2, '01'),
(20, 'dedwwww', 'unité', '2029-04-04 00:00:00', 2, '05'),
(21, '23', 'unité', NULL, 2, '01'),
(22, '43', 'paquet', '2029-04-04 00:00:00', 2, '06,09'),
(23, '35', 'unité', '2922-03-31 00:00:00', 1, ''),
(24, '3535', 'unité', NULL, 1, '');

-- --------------------------------------------------------

--
-- Table structure for table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `categorie`
--

INSERT INTO `categorie` (`id_categorie`, `nom_categorie`) VALUES
(1, 'materiel'),
(4, 'produit'),
(5, 'machine');

-- --------------------------------------------------------

--
-- Table structure for table `laboratoire`
--

DROP TABLE IF EXISTS `laboratoire`;
CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  `capacite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`, `capacite`) VALUES
(1, 'Laboratoire de Chimie', 5),
(2, 'labo cinetique', 8),
(5, 'Petrochimi', 10),
(6, 'labo MPG', 6),
(7, 'Labo Min', 3);

-- --------------------------------------------------------

--
-- Table structure for table `ligne_recu`
--

DROP TABLE IF EXISTS `ligne_recu`;
CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int NOT NULL DEFAULT '0',
  `id_recu` int NOT NULL DEFAULT '0',
  `quantite` int NOT NULL DEFAULT '0',
  `degradation_quantite` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ligne_recu`
--

INSERT INTO `ligne_recu` (`id_article`, `id_recu`, `quantite`, `degradation_quantite`) VALUES
(22, 85, 3, 1);

-- --------------------------------------------------------

--
-- Table structure for table `matiere`
--

DROP TABLE IF EXISTS `matiere`;
CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  `niveau` enum('L1','L2','L3') NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `matiere`
--

INSERT INTO `matiere` (`id_matiere`, `nom_matiere`, `niveau`) VALUES
(1, 'GCGP_41', 'L1'),
(2, 'GCGP_42', 'L3'),
(3, 'chimi cinetique', 'L1'),
(4, 'chimi', 'L3'),
(5, 'GCGP_40', 'L2'),
(6, 'GCGP_45', 'L2');

-- --------------------------------------------------------

--
-- Table structure for table `professeur`
--

DROP TABLE IF EXISTS `professeur`;
CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(15) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(3, 'yeslem', 'teghra', '23543@isme.esp.mr', '34303065'),
(4, 'asiiiiiiiii', 'a', '07@gmail.com', '00000000'),
(6, 'med', 'sidi', '23543@isme.esp.mre', '34303464'),
(7, 'Dr.ahmed', 'ahmed', 'sidahmedmeden7@gmail.com', '34303445'),
(8, 'sidahmed', 'meden', 'sidahmedmeden@gmail.com', '65323455'),
(9, 'bebouh', 'diagana', 'the9rde@gmail.com', '34304465'),
(12, 'a', 'a', '', ''),
(19, 'yghu', '87788', 'sidahmedmei8oden07@gmail.com', '44444444'),
(20, 'hhj', 'uyy', 'sidqwwi23543@isme.esp.mr', '23332222'),
(21, 'dff', 'dffd', 'sidahmedme333den07@gmail.com', '11111112');

-- --------------------------------------------------------

--
-- Table structure for table `recu`
--

DROP TABLE IF EXISTS `recu`;
CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int NOT NULL AUTO_INCREMENT,
  `date_emission` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `id_tp` int NOT NULL,
  `id_prof` int NOT NULL,
  PRIMARY KEY (`id_recu`),
  UNIQUE KEY `unique_tp` (`id_tp`),
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=86 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `recu`
--

INSERT INTO `recu` (`id_recu`, `date_emission`, `degradation`, `observations`, `id_tp`, `id_prof`) VALUES
(85, '2025-04-11 17:22:24', 0, '', 204, 8);

-- --------------------------------------------------------

--
-- Table structure for table `stock_laboratoire`
--

DROP TABLE IF EXISTS `stock_laboratoire`;
CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_lot` int NOT NULL,
  `id_laboratoire` int NOT NULL,
  `quantite` int NOT NULL,
  PRIMARY KEY (`id_lot`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `stock_laboratoire`
--

INSERT INTO `stock_laboratoire` (`id_lot`, `id_laboratoire`, `quantite`) VALUES
(5, 5, 1),
(6, 5, 1),
(6, 6, 0),
(7, 5, 1),
(7, 6, 16),
(8, 2, 9),
(8, 5, 1),
(8, 6, 7),
(9, 5, 1),
(10, 5, 1),
(11, 2, 2),
(11, 6, 0);

-- --------------------------------------------------------

--
-- Table structure for table `stock_magasin`
--

DROP TABLE IF EXISTS `stock_magasin`;
CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_lot` int NOT NULL AUTO_INCREMENT,
  `id_article` int NOT NULL,
  `quantite` int NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `date_ajout` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_lot`),
  KEY `id_article` (`id_article`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `stock_magasin`
--

INSERT INTO `stock_magasin` (`id_lot`, `id_article`, `quantite`, `date_expiration`, `date_ajout`) VALUES
(5, 7, 25, '2025-04-17 00:00:00', '2025-03-24 22:31:28'),
(6, 8, 13, NULL, '2025-03-24 22:31:52'),
(7, 9, 18, NULL, '2025-03-25 01:19:39'),
(8, 10, 17, NULL, '2025-03-25 01:28:23'),
(9, 11, 21, NULL, '2025-03-25 01:43:06'),
(10, 12, 34, NULL, '2025-03-25 07:38:16'),
(11, 13, 14, NULL, '2025-03-26 00:33:49'),
(12, 14, 2, '2025-04-18 00:00:00', '2025-04-11 00:51:07'),
(13, 15, 5, '2025-04-11 00:00:00', '2025-04-11 14:20:19'),
(16, 21, 3, NULL, '2025-04-11 15:41:51'),
(17, 22, 43, '2029-04-04 00:00:00', '2025-04-11 15:46:58'),
(18, 23, 100, '2922-03-31 00:00:00', '2025-04-13 20:26:36'),
(19, 24, 3, NULL, '2025-04-13 20:28:06');

-- --------------------------------------------------------

--
-- Table structure for table `tp`
--

DROP TABLE IF EXISTS `tp`;
CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `annee_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int NOT NULL,
  `id_matiere` int NOT NULL,
  `id_prof` int NOT NULL,
  `recu_genere` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=211 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`, `recu_genere`) VALUES
(204, 'cinetique', '2025-04-11 08:00:00', '2025-04-11 09:30:00', '2024-2025', 1, 2, 8, 1),
(205, 'cinetique', '2025-04-11 09:45:00', '2025-04-11 11:15:00', '2024-2025', 1, 2, 8, 0),
(206, 'cinetique', '2025-04-15 08:00:00', '2025-04-15 09:30:00', '2024-2025', 1, 1, 3, 0),
(207, 'cinetique', '2025-04-15 09:45:00', '2025-04-15 11:15:00', '2024-2025', 1, 1, 3, 0),
(208, 'cinetique', '2025-04-15 11:30:00', '2025-04-15 13:00:00', '2024-2025', 1, 1, 3, 0),
(209, 'cinetique', '2025-04-15 15:10:00', '2025-04-15 16:40:00', '2024-2025', 1, 1, 3, 0),
(210, 'cinetique', '2025-04-15 17:00:00', '2025-04-15 18:30:00', '2024-2025', 1, 1, 3, 0);

-- --------------------------------------------------------

--
-- Table structure for table `type`
--

DROP TABLE IF EXISTS `type`;
CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie` (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `type`
--

INSERT INTO `type` (`id_type`, `nom_type`, `id_categorie`) VALUES
(1, 'pippet', 1),
(2, 'acide', 4),
(3, 'base', 4),
(4, 'bêcher', 1),
(5, 'climatuseur', 5);

-- --------------------------------------------------------

--
-- Table structure for table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','user','super_admin') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `gmail` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `email`, `password`, `role`) VALUES
(5, 'admin', 'admin@example.com', 'scrypt:32768:8:1$PkITUqxRGMnlOiqO$d3326cbceb722ac77f6e3831bb27503503e604145406d1e6c12947359c4f9648395421bbb471459314320f9f449ad8bdaee3a9699fec7ed91bb1d5af50998add', 'admin'),
(6, 'user', 'user@example.com', 'scrypt:32768:8:1$8eOYiv0OZoQkVAjs$a162834f8313d9950b5547da4961549423e968a4b03d7b03d9c6fb815fc07efc717c8019b18e6c0a28dda15f865f97219090906d555894b94fe4153b045d3e61', 'user'),
(15, 'sidahmed2', '23543@isme.esp.mr', 'scrypt:32768:8:1$BYaOrLrN5WNpJC3Z$145644f14a585c88bdfa4e748b1f19f17d51643c1b4db2bc59d6841169c6bad7133250dc7f05b454f1345deb1d6def42fd58bbd51e77982926f72f2160ab3b58', 'admin'),
(16, '43', 'sidahmedmeden07@gmail.com', 'scrypt:32768:8:1$FWwXps6E6rXoeGKQ$1318567b2537b6f11d60cada6abf31330d56675b143e46c022f2aaccbf9238716b4db508d08e136b1e7ed91a1de1cb0f0a54869ca945735bb4e1a8266abae090', 'admin'),
(17, 'ddw42', '23542@isme.esp.mr', 'scrypt:32768:8:1$iBGKPbN71ggQDCfx$0fe34f6d15ea6830fe326ca505f345a6cbe3286c26f9099c465ab7575f430f0581f821d6cfdfb8321341708e058063d96e29ba1def6283cc9a8f707a577e0e24', 'admin'),
(18, 'Mariem', '23516@isme.esp.mr', 'scrypt:32768:8:1$iUGmrANbYE2ux5NQ$39e1f006d212088cca133480fb5906830a37f5531927e49061d8705eb49cd6a498f2d017185416f9bfcfb5c89c16d10311792ccb93fea7e4895f987516851aef', 'admin'),
(22, 'super_admin', 'admin@exemple.com', 'scrypt:32768:8:1$O9j2xLq9$c8d7e362adc18d5b0d0e5d8a1b6d4b3e6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d', 'super_admin');

--
-- Constraints for dumped tables
--

--
-- Constraints for table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_type`) REFERENCES `type` (`id_type`);

--
-- Constraints for table `ligne_recu`
--
ALTER TABLE `ligne_recu`
  ADD CONSTRAINT `ligne_recu_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `ligne_recu_ibfk_2` FOREIGN KEY (`id_recu`) REFERENCES `recu` (`id_recu`) ON DELETE CASCADE;

--
-- Constraints for table `recu`
--
ALTER TABLE `recu`
  ADD CONSTRAINT `recu_ibfk_1` FOREIGN KEY (`id_tp`) REFERENCES `tp` (`id_tp`),
  ADD CONSTRAINT `recu_ibfk_2` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `stock_laboratoire`
--
ALTER TABLE `stock_laboratoire`
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_lot`) REFERENCES `stock_magasin` (`id_lot`),
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`);

--
-- Constraints for table `stock_magasin`
--
ALTER TABLE `stock_magasin`
  ADD CONSTRAINT `stock_magasin_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`);

--
-- Constraints for table `tp`
--
ALTER TABLE `tp`
  ADD CONSTRAINT `tp_ibfk_1` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`),
  ADD CONSTRAINT `tp_ibfk_2` FOREIGN KEY (`id_matiere`) REFERENCES `matiere` (`id_matiere`),
  ADD CONSTRAINT `tp_ibfk_3` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Constraints for table `type`
--
ALTER TABLE `type`
  ADD CONSTRAINT `type_ibfk_1` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
