-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : ven. 18 avr. 2025 à 22:37
-- Version du serveur : 5.6.17
-- Version de PHP : 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `gestion_lab`
--

-- --------------------------------------------------------

--
-- Structure de la table `article`
--

DROP TABLE IF EXISTS `article`;
CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int(11) NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `id_type` int(11) NOT NULL,
  `ghs_codes` varchar(255) DEFAULT NULL,
  `sds_filename` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `article`
--

INSERT INTO `article` (`id_article`, `nom_article`, `unite_mesure`, `date_expiration`, `id_type`, `ghs_codes`, `sds_filename`) VALUES
(1, 'becher', 'litre', NULL, 1, NULL, NULL),
(2, 'meden', 'litre', NULL, 1, NULL, NULL),
(7, 'pipette 20mL', 'unité', NULL, 1, '', NULL),
(8, 'bêcher  50mL', 'unité', NULL, 4, '', NULL),
(11, 'NaOH', 'litre', NULL, 3, '06', NULL),
(15, 'sidahmed', 'kg', NULL, 1, '', NULL),
(16, 'sidahmed', 'kg', '2025-04-11 00:00:00', 1, '01,02', NULL),
(18, 'sidahmed43', 'unité', '2025-05-07 00:00:00', 2, '01', NULL),
(20, 'dedwwww', 'unité', '2029-04-04 00:00:00', 2, '05', NULL),
(21, '23', 'unité', NULL, 2, '01', NULL),
(22, '43', 'paquet', NULL, 2, '06,09', NULL),
(27, 'v', 'kg', '2040-02-09 00:00:00', 1, '', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `categorie`
--

DROP TABLE IF EXISTS `categorie`;
CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `categorie`
--

INSERT INTO `categorie` (`id_categorie`, `nom_categorie`) VALUES
(1, 'materiel'),
(4, 'produit'),
(5, 'machine');

-- --------------------------------------------------------

--
-- Structure de la table `laboratoire`
--

DROP TABLE IF EXISTS `laboratoire`;
CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int(11) NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  `capacite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`, `capacite`) VALUES
(1, 'Laboratoire de Chimie', 5),
(2, 'labo cinetique', 8),
(5, 'Petrochimi', 10),
(6, 'labo MPG', 6),
(8, 'Labo tretment thermique', 10);

-- --------------------------------------------------------

--
-- Structure de la table `ligne_recu`
--

DROP TABLE IF EXISTS `ligne_recu`;
CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int(11) NOT NULL DEFAULT '0',
  `id_recu` int(11) NOT NULL DEFAULT '0',
  `quantite` int(11) NOT NULL DEFAULT '0',
  `degradation_quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `matiere`
--

DROP TABLE IF EXISTS `matiere`;
CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int(11) NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  `niveau` enum('L1','L2','L3') NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `matiere`
--

INSERT INTO `matiere` (`id_matiere`, `nom_matiere`, `niveau`) VALUES
(10, 'gcgp31', 'L2'),
(12, 'gcgcp_33', 'L2');

-- --------------------------------------------------------

--
-- Structure de la table `professeur`
--

DROP TABLE IF EXISTS `professeur`;
CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int(11) NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(15) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(22, 'seydi', 'diagana', 'diaganaseydi02@gmail.com', '43439902'),
(23, 'sid\'ahmed', 'meden', '258848@gmail.com', '06124585'),
(26, 'dididdd', 'meden', 'fybfyubff@gmail.com', '44586587');

-- --------------------------------------------------------

--
-- Structure de la table `recu`
--

DROP TABLE IF EXISTS `recu`;
CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int(11) NOT NULL AUTO_INCREMENT,
  `date_emission` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  PRIMARY KEY (`id_recu`),
  UNIQUE KEY `unique_tp` (`id_tp`),
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `recu`
--

INSERT INTO `recu` (`id_recu`, `date_emission`, `degradation`, `observations`, `id_tp`, `id_prof`) VALUES
(1, '2025-04-16 23:21:31', 0, '', 216, 23),
(3, '2025-04-18 20:28:55', 0, '', 253, 22);

-- --------------------------------------------------------

--
-- Structure de la table `stock_laboratoire`
--

DROP TABLE IF EXISTS `stock_laboratoire`;
CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_lot` int(11) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  PRIMARY KEY (`id_lot`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `stock_laboratoire`
--

INSERT INTO `stock_laboratoire` (`id_lot`, `id_laboratoire`, `quantite`) VALUES
(5, 1, 5),
(5, 5, 1),
(6, 1, 1),
(6, 5, 1),
(6, 6, 0),
(9, 1, 1),
(9, 2, 15),
(9, 5, 1),
(13, 2, 20),
(16, 1, 1),
(17, 1, 0);

-- --------------------------------------------------------

--
-- Structure de la table `stock_magasin`
--

DROP TABLE IF EXISTS `stock_magasin`;
CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_lot` int(11) NOT NULL AUTO_INCREMENT,
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `date_expiration` datetime DEFAULT NULL,
  `date_ajout` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_lot`),
  KEY `id_article` (`id_article`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `stock_magasin`
--

INSERT INTO `stock_magasin` (`id_lot`, `id_article`, `quantite`, `date_expiration`, `date_ajout`) VALUES
(5, 7, 20, NULL, '2025-03-24 22:31:28'),
(6, 8, 10, NULL, '2025-03-24 22:31:52'),
(9, 11, 5, NULL, '2025-03-25 01:43:06'),
(13, 15, 0, NULL, '2025-04-11 14:20:19'),
(16, 21, 20, NULL, '2025-04-11 15:41:51'),
(17, 22, 22, NULL, '2025-04-11 15:46:58'),
(21, 27, 5, '2040-02-09 00:00:00', '2025-04-16 20:45:18');

-- --------------------------------------------------------

--
-- Structure de la table `tp`
--

DROP TABLE IF EXISTS `tp`;
CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int(11) NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `annee_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `id_matiere` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  `recu_genere` tinyint(1) DEFAULT '0',
  `sujet_pdf` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB AUTO_INCREMENT=255 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`, `recu_genere`, `sujet_pdf`) VALUES
(211, 'gcgp_33', '2025-04-12 08:00:00', '2025-04-12 09:30:00', '2024-2025', 6, 12, 23, 0, NULL),
(212, 'gcgp_33', '2025-04-12 09:45:00', '2025-04-12 11:15:00', '2024-2025', 6, 12, 23, 0, NULL),
(213, 'gcgp_33', '2025-04-12 11:30:00', '2025-04-12 13:00:00', '2024-2025', 6, 12, 23, 0, NULL),
(214, 'gcgp_33', '2025-04-12 15:10:00', '2025-04-12 16:40:00', '2024-2025', 6, 12, 23, 0, NULL),
(215, 'gcgp_33', '2025-04-12 17:00:00', '2025-04-12 18:30:00', '2024-2025', 6, 12, 23, 0, NULL),
(216, 'cinetique', '2025-04-16 08:00:00', '2025-04-16 09:30:00', '2024-2025', 1, 10, 23, 1, NULL),
(217, 'cinetique', '2025-04-16 09:45:00', '2025-04-16 11:15:00', '2024-2025', 1, 10, 23, 0, NULL),
(218, 'cinetique', '2025-04-16 11:30:00', '2025-04-16 13:00:00', '2024-2025', 1, 10, 23, 0, NULL),
(219, 'cinetique', '2025-04-16 15:10:00', '2025-04-16 16:40:00', '2024-2025', 1, 10, 23, 0, NULL),
(220, 'cinetique', '2025-04-16 17:00:00', '2025-04-16 18:30:00', '2024-2025', 1, 10, 23, 0, NULL),
(229, 'corrosion', '2025-04-17 09:45:00', '2025-04-17 11:15:00', '2024-2025', 6, 10, 23, 0, '1664df91818a4cb7b10dc8e2c92ee0f5_Lebron_james.pdf'),
(230, 'corrosion', '2025-04-17 08:00:00', '2025-04-17 09:30:00', '2024-2025', 6, 10, 23, 0, '0f92d76553044a468ed685b841fb334f_Projet_dron1.pdf'),
(248, 'gcgp_33', '2025-04-19 08:00:00', '2025-04-19 09:30:00', '2024-2025', 5, 10, 22, 0, '91e0b7af368b4f82b9392f9586d3ab6b_Ds.jpeg.pdf'),
(249, 'gcgp_33', '2025-04-19 09:45:00', '2025-04-19 11:15:00', '2024-2025', 5, 10, 22, 0, '91e0b7af368b4f82b9392f9586d3ab6b_Ds.jpeg.pdf'),
(250, 'gcgp_33', '2025-04-19 11:30:00', '2025-04-19 13:00:00', '2024-2025', 5, 10, 22, 0, '91e0b7af368b4f82b9392f9586d3ab6b_Ds.jpeg.pdf'),
(253, 'corrosion', '2025-04-18 08:00:00', '2025-04-18 09:30:00', '2024-2025', 1, 10, 22, 1, '46949b02ecaf4d809233ad380ff1b9e0_Ds.jpeg.pdf');

-- --------------------------------------------------------

--
-- Structure de la table `type`
--

DROP TABLE IF EXISTS `type`;
CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int(11) NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int(11) NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie` (`id_categorie`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Déchargement des données de la table `type`
--

INSERT INTO `type` (`id_type`, `nom_type`, `id_categorie`) VALUES
(1, 'pippet', 1),
(2, 'acide', 4),
(3, 'base', 4),
(4, 'bêcher', 1),
(5, 'climatuseur', 5);

-- --------------------------------------------------------

--
-- Structure de la table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(191) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','user','super_admin') NOT NULL DEFAULT 'user',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_unique` (`username`),
  UNIQUE KEY `email_unique` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `email`, `password`, `role`, `is_active`) VALUES
(5, 'admin', 'admin@example.com', 'scrypt:32768:8:1$Uy9NasYuhhZv4zyU$ea5f4bd47ff3708dd4fea9d57b03f1d0d5fc7960cd08280371c53bc2bcc4091df6ab38c7e4fd180af868b38bf0ab0f3542180cc5ce50448287483c29abb872cd', 'admin', 1),
(6, 'user', 'user@example.com', 'scrypt:32768:8:1$ycRcAS7gSsRDUZpA$583fea23b938735dc329c5292c50a4c3877c7b05c7b4f93b8d5fe13f26f45bcb20dbf578191706fd9cb07e3e0cfc9c401cee81ed6ce29dffe8075526526f7aea', 'user', 1),
(7, 'disey', 'diaganaseydi02@gmail.com', 'scrypt:32768:8:1$nLCUKNNe69KRDBs8$7d43ba10c9a27a1898d269857a27e5a60951c641cd74cced5b04666f9e7443d18670721deb24fa0721ebe730899e9900a00ac38d3bc08bc805bc1d3e19ebaa65', 'super_admin', 1),
(8, 'super_admin', 'super_admin@example.com', 'scrypt:32768:8:1$qbTHCuoMy4AdV5XO$a3d63451bd8b16c382cb4f7fc585fdbed27acb8b8711e475f6e7cfc6275cbe3d1255f8f7a91232b8633d978c548f99879134fdb1b56faeb5921abd06e4308da1', 'super_admin', 1);

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_type`) REFERENCES `type` (`id_type`);

--
-- Contraintes pour la table `ligne_recu`
--
ALTER TABLE `ligne_recu`
  ADD CONSTRAINT `ligne_recu_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `ligne_recu_ibfk_2` FOREIGN KEY (`id_recu`) REFERENCES `recu` (`id_recu`) ON DELETE CASCADE;

--
-- Contraintes pour la table `recu`
--
ALTER TABLE `recu`
  ADD CONSTRAINT `recu_ibfk_1` FOREIGN KEY (`id_tp`) REFERENCES `tp` (`id_tp`),
  ADD CONSTRAINT `recu_ibfk_2` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Contraintes pour la table `stock_laboratoire`
--
ALTER TABLE `stock_laboratoire`
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_lot`) REFERENCES `stock_magasin` (`id_lot`),
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`);

--
-- Contraintes pour la table `stock_magasin`
--
ALTER TABLE `stock_magasin`
  ADD CONSTRAINT `stock_magasin_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`);

--
-- Contraintes pour la table `tp`
--
ALTER TABLE `tp`
  ADD CONSTRAINT `tp_ibfk_1` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`),
  ADD CONSTRAINT `tp_ibfk_2` FOREIGN KEY (`id_matiere`) REFERENCES `matiere` (`id_matiere`),
  ADD CONSTRAINT `tp_ibfk_3` FOREIGN KEY (`id_prof`) REFERENCES `professeur` (`id_prof`);

--
-- Contraintes pour la table `type`
--
ALTER TABLE `type`
  ADD CONSTRAINT `type_ibfk_1` FOREIGN KEY (`id_categorie`) REFERENCES `categorie` (`id_categorie`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
