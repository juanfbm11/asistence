from rest_framework import serializers

from personas.models import Estudiante, Profesor, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    colegio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    turno = serializers.CharField(write_only=True, required=False, allow_blank=True)
    clases = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre', 'apellido', 'rol', 'password',
            'colegio', 'turno', 'clases',
        ]

    def create(self, validated_data):
        colegio = validated_data.pop('colegio', '')
        turno = validated_data.pop('turno', Profesor.TURNO_CHOICES[0][0])
        clases = validated_data.pop('clases', '')
        password = validated_data.pop('password', None)

        usuario = Usuario.objects.create_user(password=password, **validated_data)

        if usuario.rol == 'profesor':
            Profesor.objects.create(
                usuario=usuario,
                colegio=colegio,
                turno=turno,
                clases=clases,
            )
        elif usuario.rol == 'estudiante':
            Estudiante.objects.create(
                usuario=usuario,
                colegio=colegio,
                clases=clases,
            )

        return usuario

    def update(self, instance, validated_data):
        colegio = validated_data.pop('colegio', None)
        turno = validated_data.pop('turno', None)
        clases = validated_data.pop('clases', None)
        password = validated_data.pop('password', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()

        if instance.rol == 'profesor':
            perfil, _ = Profesor.objects.get_or_create(usuario=instance)
            if colegio is not None:
                perfil.colegio = colegio
            if turno is not None:
                perfil.turno = turno
            if clases is not None:
                perfil.clases = clases
            perfil.save()

        elif instance.rol == 'estudiante':
            perfil, _ = Estudiante.objects.get_or_create(usuario=instance)
            if colegio is not None:
                perfil.colegio = colegio
            if clases is not None:
                perfil.clases = clases
            perfil.save()

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['colegio'] = None
        data['turno'] = None
        data['clases'] = None

        if instance.rol == 'profesor':
            perfil = Profesor.objects.filter(usuario=instance).first()
            if perfil:
                data['colegio'] = perfil.colegio
                data['turno'] = perfil.turno
                data['clases'] = perfil.clases

        elif instance.rol == 'estudiante':
            perfil = Estudiante.objects.filter(usuario=instance).first()
            if perfil:
                data['colegio'] = perfil.colegio
                data['clases'] = perfil.clases

        return data


class ProfesorSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    nombre = serializers.CharField(source='usuario.nombre')
    apellido = serializers.CharField(source='usuario.apellido')
    email = serializers.EmailField(source='usuario.email')
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Profesor
        fields = [
            'id', 'usuario_id', 'nombre', 'apellido', 'email',
            'password', 'colegio', 'turno', 'clases',
        ]

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        password = validated_data.pop('password', None)

        usuario = Usuario.objects.create_user(
            email=usuario_data['email'],
            password=password,
            rol='profesor',
            nombre=usuario_data['nombre'],
            apellido=usuario_data['apellido'],
        )
        return Profesor.objects.create(usuario=usuario, **validated_data)

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', {})
        password = validated_data.pop('password', None)

        for field, value in usuario_data.items():
            setattr(instance.usuario, field, value)

        if password:
            instance.usuario.set_password(password)

        instance.usuario.save()

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance


class EstudianteSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    nombre = serializers.CharField(source='usuario.nombre')
    apellido = serializers.CharField(source='usuario.apellido')
    email = serializers.EmailField(source='usuario.email')
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Estudiante
        fields = [
            'id', 'usuario_id', 'nombre', 'apellido', 'email',
            'password', 'colegio', 'clases',
        ]

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        password = validated_data.pop('password', None)

        usuario = Usuario.objects.create_user(
            email=usuario_data['email'],
            password=password,
            rol='estudiante',
            nombre=usuario_data['nombre'],
            apellido=usuario_data['apellido'],
        )
        return Estudiante.objects.create(usuario=usuario, **validated_data)

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', {})
        password = validated_data.pop('password', None)

        for field, value in usuario_data.items():
            setattr(instance.usuario, field, value)

        if password:
            instance.usuario.set_password(password)

        instance.usuario.save()

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance
