# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

folder_structure = (
    (
        # title, type, exclude_from_nav, allow_discussion,
        # allowed_types,
        # layout, default_page,
        # content
        "Manual d'us", "Folder", False, False,
        ('Document', 'File', 'Folder', 'Image'),
        'folder_index_view', 'manual-dus',
        (
            # title, type, exclude_from_nav, allow_discussion, allowed_types, layout,
            # description,
            # text,
            ("Manual d'us", "Document", False, False, None, None,
                "Informació per a la creació d'ofertas i sol·licituds",
                u"""
                    """
            ),

            ("Gestor", "Folder", False, False,
                ('Document', 'File', 'Folder', 'Image'),
                None, None,
                (
                    ("Manual del gestor", "Document", False, False, None, None,
                        "Manual del gestor",
                        u"""
                            """
                    ),
                ),
            ),

            ("Professor", "Folder", False, False,
                ('Document', 'File', 'Folder', 'Image'),
                None, None,
                (
                    ("Manual del professor", "Document", False, False, None, None,
                        "Manual del professor",
                        u"""
                            """
                    ),
                ),
            ),

            ("Alumne", "Folder", False, False,
                ('Document', 'File', 'Folder', 'Image'),
                None, None,
                (
                    ("Manual de l'alumne", "Document", False, False, None, None,
                        "Manual de l'alumne",
                        u"""
                            """
                    ),
                ),
            ),
        )
    ),
)
