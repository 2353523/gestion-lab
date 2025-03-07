-- phpMyAdmin SQL Dump
-- version 4.1.14
-- http://www.phpmyadmin.net
--
-- Client :  127.0.0.1
-- Généré le :  Ven 07 Mars 2025 à 17:45
-- Version du serveur :  5.6.17
-- Version de PHP :  5.5.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données :  `gestion_lab`
--

-- --------------------------------------------------------

--
-- Structure de la table `article`
--

CREATE TABLE IF NOT EXISTS `article` (
  `id_article` int(11) NOT NULL AUTO_INCREMENT,
  `nom_article` varchar(150) NOT NULL,
  `unite_mesure` varchar(50) NOT NULL,
  `id_stock_magasin` int(11) NOT NULL,
  `id_type` int(11) NOT NULL,
  PRIMARY KEY (`id_article`),
  KEY `id_stock_magasin` (`id_stock_magasin`),
  KEY `id_type` (`id_type`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `categorie`
--

CREATE TABLE IF NOT EXISTS `categorie` (
  `id_categorie` int(11) NOT NULL AUTO_INCREMENT,
  `nom_categorie` varchar(100) NOT NULL,
  PRIMARY KEY (`id_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `emploi`
--

CREATE TABLE IF NOT EXISTS `emploi` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) NOT NULL,
  `jour` tinyint(4) NOT NULL,
  `creneau` varchar(2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `id_tp` (`id_tp`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

-- --------------------------------------------------------

--
-- Structure de la table `historique_`
--

CREATE TABLE IF NOT EXISTS `historique_` (
  `id_historique` int(11) NOT NULL AUTO_INCREMENT,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `id_article` int(11) NOT NULL,
  `quantite` int(11) NOT NULL DEFAULT '0',
  `date_utilisation` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `commentaire` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historique`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `laboratoire`
--

CREATE TABLE IF NOT EXISTS `laboratoire` (
  `id_laboratoire` int(11) NOT NULL AUTO_INCREMENT,
  `nom_laboratoire` varchar(50) NOT NULL,
  PRIMARY KEY (`id_laboratoire`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

--
-- Contenu de la table `laboratoire`
--

INSERT INTO `laboratoire` (`id_laboratoire`, `nom_laboratoire`) VALUES
(1, 'Laboratoire de Chimie');

-- --------------------------------------------------------

--
-- Structure de la table `ligne_recu`
--

CREATE TABLE IF NOT EXISTS `ligne_recu` (
  `id_article` int(11) NOT NULL DEFAULT '0',
  `id_recu` int(11) NOT NULL DEFAULT '0',
  `quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_recu`),
  KEY `id_recu` (`id_recu`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `matiere`
--

CREATE TABLE IF NOT EXISTS `matiere` (
  `id_matiere` int(11) NOT NULL AUTO_INCREMENT,
  `nom_matiere` varchar(100) NOT NULL,
  PRIMARY KEY (`id_matiere`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=8 ;

--
-- Contenu de la table `matiere`
--

INSERT INTO `matiere` (`id_matiere`, `nom_matiere`) VALUES
(1, 'gcgp35'),
(3, 'gcgp_'),
(6, 'gcgp31'),
(7, 'gcgp32');

-- --------------------------------------------------------

--
-- Structure de la table `professeur`
--

CREATE TABLE IF NOT EXISTS `professeur` (
  `id_prof` int(11) NOT NULL AUTO_INCREMENT,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `telephone` varchar(15) NOT NULL,
  PRIMARY KEY (`id_prof`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `telephone` (`telephone`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=3 ;

--
-- Contenu de la table `professeur`
--

INSERT INTO `professeur` (`id_prof`, `prenom`, `nom`, `email`, `telephone`) VALUES
(1, 'diagana', 'seydi', 'diaganseydi02@gmail.com', '06124585'),
(2, 'sid''ahmed', 'meden', '23543@gmail.com', '45124563');

-- --------------------------------------------------------

--
-- Structure de la table `recu`
--

CREATE TABLE IF NOT EXISTS `recu` (
  `id_recu` int(11) NOT NULL AUTO_INCREMENT,
  `date_emission` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `degradation` tinyint(1) NOT NULL DEFAULT '0',
  `observations` varchar(255) DEFAULT NULL,
  `id_tp` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  PRIMARY KEY (`id_recu`),
  KEY `id_tp` (`id_tp`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `stock_laboratoire`
--

CREATE TABLE IF NOT EXISTS `stock_laboratoire` (
  `id_article` int(11) NOT NULL DEFAULT '0',
  `id_laboratoire` int(11) NOT NULL DEFAULT '0',
  `quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_article`,`id_laboratoire`),
  KEY `id_laboratoire` (`id_laboratoire`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `stock_magasin`
--

CREATE TABLE IF NOT EXISTS `stock_magasin` (
  `id_stock_magasin` int(11) NOT NULL AUTO_INCREMENT,
  `quantite` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_stock_magasin`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `tp`
--

CREATE TABLE IF NOT EXISTS `tp` (
  `id_tp` int(11) NOT NULL AUTO_INCREMENT,
  `nom_tp` varchar(100) NOT NULL,
  `heure_debut` datetime NOT NULL,
  `heure_fin` datetime NOT NULL,
  `annee_scolaire` varchar(9) NOT NULL,
  `id_laboratoire` int(11) NOT NULL,
  `id_matiere` int(11) NOT NULL,
  `id_prof` int(11) NOT NULL,
  PRIMARY KEY (`id_tp`),
  KEY `id_laboratoire` (`id_laboratoire`),
  KEY `id_matiere` (`id_matiere`),
  KEY `id_prof` (`id_prof`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=22 ;

--
-- Contenu de la table `tp`
--

INSERT INTO `tp` (`id_tp`, `nom_tp`, `heure_debut`, `heure_fin`, `annee_scolaire`, `id_laboratoire`, `id_matiere`, `id_prof`) VALUES
(5, 'moi', '2025-11-12 14:00:00', '2025-11-12 15:00:00', '', 1, 1, 1),
(6, 'moi', '2025-03-15 15:00:00', '2025-03-15 16:01:00', '', 1, 1, 1),
(7, 'moi', '2025-03-01 16:00:00', '2025-03-01 17:00:00', '2024-2025', 1, 1, 1),
(8, 'corrosion', '2025-03-02 17:46:00', '2025-03-02 23:50:00', '2024-2025', 1, 1, 2),
(9, 'moi', '2025-03-03 15:00:00', '2025-03-03 17:06:00', '2024-2025', 1, 1, 1),
(10, 'moi', '2025-03-04 15:12:00', '2025-03-04 16:14:00', '2024-2025', 1, 1, 1),
(13, 'corrosion', '2025-03-05 15:10:00', '2025-03-05 16:40:00', '2024-2025', 1, 1, 1),
(17, 'corrosion', '2025-03-07 11:30:00', '2025-03-07 13:00:00', '2024-2025', 1, 3, 1),
(20, 'corrosion', '2025-03-07 08:00:00', '2025-03-07 18:30:00', '2025-2026', 1, 1, 2),
(21, 'corrosion', '2025-03-08 15:10:00', '2025-03-08 16:40:00', '2024-2025', 1, 1, 1);

-- --------------------------------------------------------

--
-- Structure de la table `type`
--

CREATE TABLE IF NOT EXISTS `type` (
  `id_type` int(11) NOT NULL AUTO_INCREMENT,
  `nom_type` varchar(50) NOT NULL,
  `id_categorie` int(11) NOT NULL,
  PRIMARY KEY (`id_type`),
  KEY `id_categorie` (`id_categorie`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Structure de la table `utilisateur`
--

CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('admin','user') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=3 ;

--
-- Contenu de la table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `username`, `password`, `role`) VALUES
(1, 'admin', 'scrypt:32768:8:1$rkpkHCNutBHs3SVB$d12470ea3d4be77c06195f0947400d2107d28cc7ec2bff61f8b4c2e19740c875104d864d11509ab7760abb8d95fbf3903db237e9776494462f99f3440f4fa109', 'admin'),
(2, 'user', 'scrypt:32768:8:1$aGYiKRgvvcZ0S3FN$b82fa992d132278f95637d8eccdde4d941b207bc8e546983a5a74e857137e00f96a04730e1210d93c6fc5ef76e7d4da43d9124cdc84e1ecdfb98ffb147b79f20', 'user');

--
-- Contraintes pour les tables exportées
--

--
-- Contraintes pour la table `article`
--
ALTER TABLE `article`
  ADD CONSTRAINT `article_ibfk_1` FOREIGN KEY (`id_stock_magasin`) REFERENCES `stock_magasin` (`id_stock_magasin`),
  ADD CONSTRAINT `article_ibfk_2` FOREIGN KEY (`id_type`) REFERENCES `type` (`id_type`);

--
-- Contraintes pour la table `emploi`
--
ALTER TABLE `emploi`
  ADD CONSTRAINT `emploi_ibfk_1` FOREIGN KEY (`id_tp`) REFERENCES `tp` (`id_tp`);

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
  ADD CONSTRAINT `stock_laboratoire_ibfk_1` FOREIGN KEY (`id_article`) REFERENCES `article` (`id_article`) ON DELETE CASCADE,
  ADD CONSTRAINT `stock_laboratoire_ibfk_2` FOREIGN KEY (`id_laboratoire`) REFERENCES `laboratoire` (`id_laboratoire`) ON DELETE CASCADE;

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

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
