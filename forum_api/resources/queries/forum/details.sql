SELECT 
		forum.id, 
		forum.name, 
		forum.slug, 
		user.about, 
		user.email, 
		user.id AS 'user_id', 
		user.isAnonymous, 
		user.name AS 'user_name', 
		user.username AS 'username' 
	FROM forum, user 
	WHERE forum.user=user.email AND forum.slug='{0}';

SELECT * FROM follower WHERE follower_mail='{0}';

SELECT * FROM follower WHERE following_mail='{0}';

SELECT * FROM subscribe WHERE user='{0}';

SELECT * FROM forum WHERE slug='forum1';
