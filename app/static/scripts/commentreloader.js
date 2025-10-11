document.addEventListener('DOMContentLoaded', function () {
    const submitButton = document.getElementById('submitb');
    const commentField = document.getElementById('comment');
    const postId = document.getElementById('post_id').value;
    const commentList = document.getElementById('commentlist');
    const likeButton = document.getElementById('likebtn');

    likeButton.addEventListener('click', function (event)
    {
        event.preventDefault();
        likeButton.disabled = true;

        fetch('/projects/likepost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({id: postId }),
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('likebtn').textContent = data.btn_text + " " + data.number;
        })
        .catch(error => console.error('Error submitting like:', error))
        .finally(() => {
            likeButton.disabled = false;
        });
    });


    // Submit a new comment
    submitButton.addEventListener('click', function (event) {
        event.preventDefault();

        const commentText = commentField.value.trim();
        if (!commentText) {
            alert("Please enter a comment before submitting.");
            return;
        }

        submitButton.disabled = true;

        fetch('/projects/processcomments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ comment: commentText, id: postId }),
        })
        .then(response => response.json())
        .then(data => {
            commentList.innerHTML = data.html;
            commentField.value = '';
            attachDeleteHandlers(); // Re-bind delete buttons
            commentList.scrollTop = commentList.scrollHeight;
        })
        .catch(error => console.error('Error submitting comment:', error))
        .finally(() => {
            submitButton.disabled = false;
        });
    });

    // Delete a comment
    function attachCommentDeleteHandlers() {
        document.querySelectorAll('.delete-comment').forEach(button => {
            button.addEventListener('click', function () {
                const commentId = this.getAttribute('data-comment-id');

                fetch(`/projects/commentdelete/${commentId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to delete comment');
                    }
                    return fetch('/projects/processcomments', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ comment: '', id: postId })
                    });
                })
                .then(response => response.json())
                .then(data => {
                    commentList.innerHTML = data.html;
                    attachCommentDeleteHandlers(); // Re-bind after update
                })
                .catch(error => console.error('Error deleting comment:', error));
            });
        });
    };

    function attachCommentLikeHandlers() {
        document.querySelectorAll('.like-comment').forEach(button => {
            button.addEventListener('click', function () {
                const commentId = this.getAttribute('data-comment-id');

                fetch('/projects/likecomment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ comment_id: commentId }),
                })
                .then(response => response.json())
                .then(data => {
                    button.textContent = data.btn_text + " " + data.number ;
                })
                .catch(error => console.error('Error submitting like:', error))
                .finally(() => {
                    likeButton.disabled = false;
                });
            });
        });
    };

    // Initial binding
    attachCommentDeleteHandlers();
    attachCommentLikeHandlers();
});